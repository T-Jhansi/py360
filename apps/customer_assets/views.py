"""
Views for Customer Assets app.
"""

from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from apps.core.pagination import StandardResultsSetPagination
from .models import CustomerAssets
from .serializers import (
    CustomerAssetsSerializer,
    CustomerAssetsCreateSerializer,
    CustomerAssetsUpdateSerializer,
    CustomerAssetsListSerializer
)


class CustomerAssetsListCreateView(generics.ListCreateAPIView):
    """
    List all customer assets or create a new one.
    """
    queryset = CustomerAssets.objects.filter(is_deleted=False)
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CustomerAssetsCreateSerializer
        return CustomerAssetsListSerializer
    
    def get_queryset(self):
        queryset = CustomerAssets.objects.filter(is_deleted=False)
        
        # Filter by customer
        customer_id = self.request.query_params.get('customer_id')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        
        # Filter by residence type
        residence_type = self.request.query_params.get('residence_type')
        if residence_type:
            queryset = queryset.filter(residence_type=residence_type)
        
        # Filter by residence status
        residence_status = self.request.query_params.get('residence_status')
        if residence_status:
            queryset = queryset.filter(residence_status=residence_status)
        
        # Filter by residence rating
        residence_rating = self.request.query_params.get('residence_rating')
        if residence_rating:
            queryset = queryset.filter(residence_rating=residence_rating)
        
        # Search by customer name, code, or location
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(customer__first_name__icontains=search) |
                Q(customer__last_name__icontains=search) |
                Q(customer__company_name__icontains=search) |
                Q(customer__customer_code__icontains=search) |
                Q(residence_location__icontains=search)
            )
        
        return queryset.select_related('customer').order_by('-created_at')
    
    def perform_create(self, serializer):
        """Create customer assets"""
        serializer.save(created_by=self.request.user)


class CustomerAssetsDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete customer assets.
    """
    queryset = CustomerAssets.objects.filter(is_deleted=False)
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return CustomerAssetsUpdateSerializer
        return CustomerAssetsSerializer
    
    def perform_update(self, serializer):
        """Update customer assets"""
        serializer.save(updated_by=self.request.user)
    
    def perform_destroy(self, instance):
        """Soft delete the customer assets"""
        instance.delete(user=self.request.user)


@api_view(['GET'])
def customer_assets_by_customer(request, customer_id):
    """
    Get all assets for a specific customer.
    """
    assets = CustomerAssets.objects.filter(
        customer_id=customer_id,
        is_deleted=False
    )
    serializer = CustomerAssetsListSerializer(assets, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def customer_assets_statistics(request):
    """
    Get statistics about customer assets.
    """
    assets = CustomerAssets.objects.filter(is_deleted=False)
    
    # Residence type distribution
    type_distribution = {}
    for choice in CustomerAssets.RESIDENCE_TYPE_CHOICES:
        type_key = choice[0]
        count = assets.filter(residence_type=type_key).count()
        type_distribution[type_key] = count
    
    # Residence status distribution
    status_distribution = {}
    for choice in CustomerAssets.RESIDENCE_STATUS_CHOICES:
        status_key = choice[0]
        count = assets.filter(residence_status=status_key).count()
        status_distribution[status_key] = count
    
    # Residence rating distribution
    rating_distribution = {}
    for choice in CustomerAssets.RESIDENCE_RATING_CHOICES:
        rating_key = choice[0]
        count = assets.filter(residence_rating=rating_key).count()
        rating_distribution[rating_key] = count
    
    # Asset score distribution
    asset_scores = [asset.asset_score for asset in assets]
    score_ranges = {
        'low': len([s for s in asset_scores if s < 10]),
        'medium': len([s for s in asset_scores if 10 <= s < 20]),
        'high': len([s for s in asset_scores if s >= 20]),
    }
    
    return Response({
        'total_assets': assets.count(),
        'residence_type_distribution': type_distribution,
        'residence_status_distribution': status_distribution,
        'residence_rating_distribution': rating_distribution,
        'asset_score_distribution': score_ranges,
    })
