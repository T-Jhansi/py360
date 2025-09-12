from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from .models import Offer
from .serializers import OfferSerializer, OfferCreateSerializer, OfferUpdateSerializer


class OfferViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing offers
    Provides CRUD operations for offers that are common to all customers
    """
    queryset = Offer.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['offer_type', 'is_active', 'currency']
    search_fields = ['title', 'description', 'features']
    ordering_fields = ['title', 'display_order', 'created_at', 'amount']
    ordering = ['display_order', 'created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return OfferCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return OfferUpdateSerializer
        return OfferSerializer
    
    def get_queryset(self):
        """Filter queryset based on query parameters"""
        queryset = super().get_queryset()
        
        # Filter by active offers only if requested
        active_only = self.request.query_params.get('active_only', 'false').lower() == 'true'
        if active_only:
            queryset = queryset.filter(is_active=True)
        
        # Filter by currently active offers (considering dates)
        currently_active = self.request.query_params.get('currently_active', 'false').lower() == 'true'
        if currently_active:
            from django.utils import timezone
            now = timezone.now()
            queryset = queryset.filter(
                is_active=True,
                start_date__lte=now,
                end_date__gte=now
            ).union(
                queryset.filter(
                    is_active=True,
                    start_date__isnull=True,
                    end_date__isnull=True
                )
            )
        
        return queryset
    
    @action(detail=False, methods=['get'], url_path='active-offers')
    def active_offers(self, request):
        """Get all currently active offers"""
        try:
            from django.utils import timezone
            now = timezone.now()
            
            # Get offers that are currently active
            offers = self.get_queryset().filter(
                is_active=True
            ).filter(
                Q(start_date__isnull=True) | Q(start_date__lte=now)
            ).filter(
                Q(end_date__isnull=True) | Q(end_date__gte=now)
            ).order_by('display_order', 'created_at')
            
            serializer = self.get_serializer(offers, many=True)
            return Response({
                'success': True,
                'message': 'Active offers retrieved successfully',
                'data': serializer.data,
                'count': offers.count()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error retrieving active offers: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='by-type/(?P<offer_type>[^/.]+)')
    def by_type(self, request, offer_type=None):
        """Get offers by type (payment_option, product, bundle, etc.)"""
        try:
            if not offer_type:
                return Response({
                    'success': False,
                    'message': 'Offer type parameter is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate offer type
            valid_types = [choice[0] for choice in Offer.OFFER_TYPE_CHOICES]
            if offer_type not in valid_types:
                return Response({
                    'success': False,
                    'message': f'Invalid offer type. Must be one of: {", ".join(valid_types)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            offers = self.get_queryset().filter(offer_type=offer_type)
            serializer = self.get_serializer(offers, many=True)
            
            return Response({
                'success': True,
                'message': f'Offers for type "{offer_type}" retrieved successfully',
                'data': serializer.data,
                'count': offers.count()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error retrieving offers by type: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def create(self, request, *args, **kwargs):
        """Create a new offer"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        
        return Response({
            'success': True,
            'message': 'Offer created successfully',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED, headers=headers)
    
    def update(self, request, *args, **kwargs):
        """Update an existing offer"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'success': True,
            'message': 'Offer updated successfully',
            'data': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        """Delete an offer (soft delete)"""
        instance = self.get_object()
        self.perform_destroy(instance)
        
        return Response({
            'success': True,
            'message': 'Offer deleted successfully',
            'data': None
        }, status=status.HTTP_204_NO_CONTENT)
    
    def list(self, request, *args, **kwargs):
        """List all offers with filtering and pagination"""
        queryset = self.filter_queryset(self.get_queryset())
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'message': 'Offers retrieved successfully',
            'data': serializer.data,
            'count': queryset.count()
        }, status=status.HTTP_200_OK)