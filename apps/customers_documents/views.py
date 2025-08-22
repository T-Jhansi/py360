from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import CustomerDocument
from .serializers import (
    CustomerDocumentSerializer,
    CustomerDocumentListSerializer,
    CustomerDocumentCreateSerializer
)
from apps.customers.models import Customer


class CustomerDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing customer documents"""
    
    queryset = CustomerDocument.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'document_type', 'is_verified', 'customer', 'verified_by'
    ]
    search_fields = [
        'document_number', 'issuing_authority', 'notes', 'verification_notes',
        'customer__first_name', 'customer__last_name', 'customer__customer_code'
    ]
    ordering_fields = [
        'created_at', 'updated_at', 'verified_at', 'expiry_date', 'issue_date'
    ]
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return CustomerDocumentListSerializer
        elif self.action == 'create':
            return CustomerDocumentCreateSerializer
        return CustomerDocumentSerializer
    
    def perform_create(self, serializer):
        """Set created_by when creating a new document"""
        serializer.save(created_by=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Create a new customer document with success message"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        return Response({
            'success': True,
            'message': 'Customer document created successfully',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED, headers=headers)

    def list(self, request, *args, **kwargs):
        """List customer documents with success message"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'success': True,
                'message': 'Customer documents retrieved successfully',
                'data': serializer.data
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'message': 'Customer documents retrieved successfully',
            'count': queryset.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a customer document with success message"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'message': 'Customer document retrieved successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        """Update a customer document with success message"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response({
            'success': True,
            'message': 'Customer document updated successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def perform_update(self, serializer):
        """Set updated_by when updating a document"""
        serializer.save(updated_by=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete a customer document with success message"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'success': True,
            'message': 'Customer document deleted successfully'
        }, status=status.HTTP_200_OK)

    def perform_destroy(self, instance):
        """Soft delete the document"""
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.deleted_by = self.request.user
        instance.save()
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify a customer document"""
        document = self.get_object()
        
        verification_notes = request.data.get('verification_notes', '')
        
        document.is_verified = True
        document.verified_at = timezone.now()
        document.verified_by = request.user
        document.verification_notes = verification_notes
        document.updated_by = request.user
        document.save()
        
        serializer = self.get_serializer(document)
        return Response({
            'success': True,
            'message': 'Document verified successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def unverify(self, request, pk=None):
        """Unverify a customer document"""
        document = self.get_object()
        
        verification_notes = request.data.get('verification_notes', '')
        
        document.is_verified = False
        document.verified_at = None
        document.verified_by = None
        document.verification_notes = verification_notes
        document.updated_by = request.user
        document.save()
        
        serializer = self.get_serializer(document)
        return Response({
            'success': True,
            'message': 'Document verification removed successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def expired(self, request):
        """Get all expired documents"""
        expired_docs = self.get_queryset().filter(
            expiry_date__lt=timezone.now().date()
        ).exclude(expiry_date__isnull=True)
        
        serializer = CustomerDocumentListSerializer(expired_docs, many=True)
        return Response({
            'success': True,
            'count': expired_docs.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Get documents expiring within 30 days"""
        from datetime import timedelta
        warning_date = timezone.now().date() + timedelta(days=30)
        
        expiring_docs = self.get_queryset().filter(
            expiry_date__lte=warning_date,
            expiry_date__gte=timezone.now().date()
        )
        
        serializer = CustomerDocumentListSerializer(expiring_docs, many=True)
        return Response({
            'success': True,
            'count': expiring_docs.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def unverified(self, request):
        """Get all unverified documents"""
        unverified_docs = self.get_queryset().filter(is_verified=False)
        
        serializer = CustomerDocumentListSerializer(unverified_docs, many=True)
        return Response({
            'success': True,
            'count': unverified_docs.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='customer/(?P<customer_id>[^/.]+)')
    def by_customer(self, request, customer_id=None):
        """Get all documents for a specific customer"""
        customer = get_object_or_404(Customer, id=customer_id, is_deleted=False)
        documents = self.get_queryset().filter(customer=customer)
        
        serializer = CustomerDocumentListSerializer(documents, many=True)
        return Response({
            'success': True,
            'customer': {
                'id': customer.id,
                'name': customer.full_name,
                'customer_code': customer.customer_code
            },
            'count': documents.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)
