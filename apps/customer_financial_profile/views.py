from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from apps.core.pagination import StandardResultsSetPagination
from .models import CustomerFinancialProfile
from .serializers import (
    CustomerFinancialProfileSerializer,
    CustomerFinancialProfileCreateSerializer,
    CustomerFinancialProfileUpdateSerializer,
    CustomerFinancialProfileListSerializer
)


class CustomerFinancialProfileListCreateView(generics.ListCreateAPIView):
    """
    List all customer financial profiles or create a new one.
    """
    queryset = CustomerFinancialProfile.objects.filter(is_deleted=False)
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CustomerFinancialProfileCreateSerializer
        return CustomerFinancialProfileListSerializer
    
    def get_queryset(self):
        queryset = CustomerFinancialProfile.objects.filter(is_deleted=False)
        
        # Filter by customer
        customer_id = self.request.query_params.get('customer_id')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        
        # Filter by risk profile
        risk_profile = self.request.query_params.get('risk_profile')
        if risk_profile:
            queryset = queryset.filter(risk_profile=risk_profile)
        
        # Filter by income range
        min_income = self.request.query_params.get('min_income')
        max_income = self.request.query_params.get('max_income')
        if min_income:
            queryset = queryset.filter(annual_income__gte=min_income)
        if max_income:
            queryset = queryset.filter(annual_income__lte=max_income)
        
        # Search by customer name or code
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(customer__first_name__icontains=search) |
                Q(customer__last_name__icontains=search) |
                Q(customer__company_name__icontains=search) |
                Q(customer__customer_code__icontains=search)
            )
        
        return queryset.select_related('customer').order_by('-created_at')
    
    def perform_create(self, serializer):
        """Create financial profile and update capacity utilization"""
        financial_profile = serializer.save(created_by=self.request.user)
        financial_profile.update_capacity_utilization()


class CustomerFinancialProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a customer financial profile.
    """
    queryset = CustomerFinancialProfile.objects.filter(is_deleted=False)
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return CustomerFinancialProfileUpdateSerializer
        return CustomerFinancialProfileSerializer
    
    def perform_update(self, serializer):
        """Update financial profile and recalculate capacity utilization"""
        financial_profile = serializer.save(updated_by=self.request.user)
        financial_profile.update_capacity_utilization()
    
    def perform_destroy(self, instance):
        """Soft delete the financial profile"""
        instance.delete(user=self.request.user)


@api_view(['GET'])
def customer_financial_profile_by_customer(request, customer_id):
    """
    Get financial profile for a specific customer.
    """
    try:
        financial_profile = CustomerFinancialProfile.objects.get(
            customer_id=customer_id,
            is_deleted=False
        )
        serializer = CustomerFinancialProfileSerializer(financial_profile)
        return Response(serializer.data)
    except CustomerFinancialProfile.DoesNotExist:
        return Response(
            {'error': 'Financial profile not found for this customer'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
def update_capacity_utilization(request, pk):
    """
    Manually update capacity utilization for a financial profile.
    """
    financial_profile = get_object_or_404(
        CustomerFinancialProfile,
        pk=pk,
        is_deleted=False
    )
    
    financial_profile.update_capacity_utilization()
    
    serializer = CustomerFinancialProfileSerializer(financial_profile)
    return Response({
        'message': 'Capacity utilization updated successfully',
        'data': serializer.data
    })


@api_view(['GET'])
def financial_profile_statistics(request):
    """
    Get statistics about customer financial profiles.
    """
    profiles = CustomerFinancialProfile.objects.filter(is_deleted=False)
    
    # Risk profile distribution
    risk_distribution = {}
    for choice in CustomerFinancialProfile.RISK_PROFILE_CHOICES:
        risk_key = choice[0]
        count = profiles.filter(risk_profile=risk_key).count()
        risk_distribution[risk_key] = count
    
    # Income range distribution
    income_ranges = {
        'low': profiles.filter(annual_income__lt=300000).count(),
        'medium': profiles.filter(
            annual_income__gte=300000,
            annual_income__lt=1000000
        ).count(),
        'high': profiles.filter(
            annual_income__gte=1000000,
            annual_income__lt=2500000
        ).count(),
        'very_high': profiles.filter(annual_income__gte=2500000).count(),
        'unknown': profiles.filter(annual_income__isnull=True).count(),
    }
    
    # Capacity utilization distribution
    capacity_ranges = {
        'low': profiles.filter(policy_capacity_utilization__lt=25).count(),
        'medium': profiles.filter(
            policy_capacity_utilization__gte=25,
            policy_capacity_utilization__lt=50
        ).count(),
        'high': profiles.filter(
            policy_capacity_utilization__gte=50,
            policy_capacity_utilization__lt=75
        ).count(),
        'near_full': profiles.filter(policy_capacity_utilization__gte=75).count(),
        'unknown': profiles.filter(policy_capacity_utilization__isnull=True).count(),
    }
    
    return Response({
        'total_profiles': profiles.count(),
        'risk_profile_distribution': risk_distribution,
        'income_range_distribution': income_ranges,
        'capacity_utilization_distribution': capacity_ranges,
    })
