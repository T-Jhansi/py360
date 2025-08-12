from rest_framework import viewsets, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import PolicyCondition
from .serializers import PolicyConditionSerializer, PolicyConditionListSerializer
from apps.core.pagination import StandardResultsSetPagination


class PolicyConditionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing policy conditions - only store and list actions"""

    queryset = PolicyCondition.objects.select_related(
        'policy', 'policy__customer', 'created_by', 'updated_by'
    ).filter(is_deleted=False)

    serializer_class = PolicyConditionSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = ['policy', 'policy__policy_number', 'policy__customer']
    search_fields = ['description', 'policy__policy_number', 'policy__customer__full_name']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    # Override to only allow create and list actions
    http_method_names = ['get', 'post']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return PolicyConditionListSerializer
        return PolicyConditionSerializer
    
    def perform_create(self, serializer):
        """Set created_by when creating a new policy condition"""
        serializer.save(created_by=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Create a new policy condition"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response({
            'success': True,
            'message': 'Policy condition created successfully',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def list(self, request, *args, **kwargs):
        """List all policy conditions with filtering and pagination"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'success': True,
                'message': 'Policy conditions retrieved successfully',
                'data': serializer.data
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'message': 'Policy conditions retrieved successfully',
            'data': serializer.data
        })
    
    # Override other methods to prevent them from being used
    def retrieve(self, request, *args, **kwargs):
        """Retrieve action is not allowed"""
        return Response({
            'success': False,
            'message': 'Retrieve action is not supported for policy conditions'
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def update(self, request, *args, **kwargs):
        """Update action is not allowed"""
        return Response({
            'success': False,
            'message': 'Update action is not supported for policy conditions'
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def partial_update(self, request, *args, **kwargs):
        """Partial update action is not allowed"""
        return Response({
            'success': False,
            'message': 'Partial update action is not supported for policy conditions'
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def destroy(self, request, *args, **kwargs):
        """Delete action is not allowed"""
        return Response({
            'success': False,
            'message': 'Delete action is not supported for policy conditions'
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)
