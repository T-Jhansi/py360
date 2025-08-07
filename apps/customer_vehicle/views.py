"""
Views for Customer Vehicle app.
"""

from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Sum, Count
from apps.core.pagination import StandardResultsSetPagination
from .models import CustomerVehicle
from .serializers import (
    CustomerVehicleSerializer,
    CustomerVehicleCreateSerializer,
    CustomerVehicleUpdateSerializer,
    CustomerVehicleListSerializer
)


class CustomerVehicleListCreateView(generics.ListCreateAPIView):
    """
    List all customer vehicles or create a new one.
    """
    queryset = CustomerVehicle.objects.filter(is_deleted=False)
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CustomerVehicleCreateSerializer
        return CustomerVehicleListSerializer
    
    def get_queryset(self):
        queryset = CustomerVehicle.objects.filter(is_deleted=False)
        
        # Filter by customer assets
        customer_assets_id = self.request.query_params.get('customer_assets_id')
        if customer_assets_id:
            queryset = queryset.filter(customer_assets_id=customer_assets_id)
        
        # Filter by customer
        customer_id = self.request.query_params.get('customer_id')
        if customer_id:
            queryset = queryset.filter(customer_assets__customer_id=customer_id)
        
        # Filter by vehicle type
        vehicle_type = self.request.query_params.get('vehicle_type')
        if vehicle_type:
            queryset = queryset.filter(vehicle_type=vehicle_type)
        
        # Filter by fuel type
        fuel_type = self.request.query_params.get('fuel_type')
        if fuel_type:
            queryset = queryset.filter(fuel_type=fuel_type)
        
        # Filter by condition
        condition = self.request.query_params.get('condition')
        if condition:
            queryset = queryset.filter(condition=condition)
        
        # Filter by model year range
        min_year = self.request.query_params.get('min_year')
        max_year = self.request.query_params.get('max_year')
        if min_year:
            queryset = queryset.filter(model_year__gte=min_year)
        if max_year:
            queryset = queryset.filter(model_year__lte=max_year)
        
        # Filter by value range
        min_value = self.request.query_params.get('min_value')
        max_value = self.request.query_params.get('max_value')
        if min_value:
            queryset = queryset.filter(value__gte=min_value)
        if max_value:
            queryset = queryset.filter(value__lte=max_value)
        
        # Search by vehicle name, registration, customer name, or code
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(vehicle_name__icontains=search) |
                Q(registration_number__icontains=search) |
                Q(customer_assets__customer__first_name__icontains=search) |
                Q(customer_assets__customer__last_name__icontains=search) |
                Q(customer_assets__customer__company_name__icontains=search) |
                Q(customer_assets__customer__customer_code__icontains=search)
            )
        
        return queryset.select_related('customer_assets__customer').order_by('-created_at')
    
    def perform_create(self, serializer):
        """Create customer vehicle"""
        serializer.save(created_by=self.request.user)


class CustomerVehicleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete customer vehicle.
    """
    queryset = CustomerVehicle.objects.filter(is_deleted=False)
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return CustomerVehicleUpdateSerializer
        return CustomerVehicleSerializer
    
    def perform_update(self, serializer):
        """Update customer vehicle"""
        serializer.save(updated_by=self.request.user)
    
    def perform_destroy(self, instance):
        """Soft delete the customer vehicle"""
        instance.delete(user=self.request.user)


@api_view(['GET'])
def customer_vehicles_by_customer_assets(request, customer_assets_id):
    """
    Get all vehicles for a specific customer assets record.
    """
    vehicles = CustomerVehicle.objects.filter(
        customer_assets_id=customer_assets_id,
        is_deleted=False
    )
    serializer = CustomerVehicleListSerializer(vehicles, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def customer_vehicles_by_customer(request, customer_id):
    """
    Get all vehicles for a specific customer.
    """
    vehicles = CustomerVehicle.objects.filter(
        customer_assets__customer_id=customer_id,
        is_deleted=False
    )
    serializer = CustomerVehicleListSerializer(vehicles, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def customer_vehicle_statistics(request):
    """
    Get statistics about customer vehicles.
    """
    vehicles = CustomerVehicle.objects.filter(is_deleted=False)
    
    # Vehicle type distribution
    type_distribution = {}
    for choice in CustomerVehicle.VEHICLE_TYPE_CHOICES:
        type_key = choice[0]
        count = vehicles.filter(vehicle_type=type_key).count()
        type_distribution[type_key] = count
    
    # Fuel type distribution
    fuel_distribution = {}
    for choice in CustomerVehicle.FUEL_TYPE_CHOICES:
        fuel_key = choice[0]
        count = vehicles.filter(fuel_type=fuel_key).count()
        fuel_distribution[fuel_key] = count
    
    # Condition distribution
    condition_distribution = {}
    for choice in CustomerVehicle.CONDITION_CHOICES:
        condition_key = choice[0]
        count = vehicles.filter(condition=condition_key).count()
        condition_distribution[condition_key] = count
    
    # Age distribution
    age_ranges = {
        'new': vehicles.filter(model_year__gte=2022).count(),
        'recent': vehicles.filter(model_year__gte=2018, model_year__lt=2022).count(),
        'moderate': vehicles.filter(model_year__gte=2010, model_year__lt=2018).count(),
        'old': vehicles.filter(model_year__lt=2010).count(),
    }
    
    # Value distribution
    value_ranges = {
        'luxury': vehicles.filter(value__gte=1000000).count(),  # 10 lakh+
        'premium': vehicles.filter(value__gte=500000, value__lt=1000000).count(),  # 5-10 lakh
        'mid_range': vehicles.filter(value__gte=200000, value__lt=500000).count(),  # 2-5 lakh
        'budget': vehicles.filter(value__lt=200000).count(),  # Below 2 lakh
    }
    
    # Vehicle score distribution
    vehicle_scores = [vehicle.vehicle_score for vehicle in vehicles]
    score_ranges = {
        'excellent': len([s for s in vehicle_scores if s >= 30]),
        'good': len([s for s in vehicle_scores if 20 <= s < 30]),
        'average': len([s for s in vehicle_scores if 10 <= s < 20]),
        'poor': len([s for s in vehicle_scores if s < 10]),
    }
    
    # Aggregate statistics
    aggregates = vehicles.aggregate(
        total_value=Sum('value'),
        average_value=Avg('value'),
        average_age=Avg('model_year'),
        total_vehicles=Count('id')
    )
    
    return Response({
        'total_vehicles': aggregates['total_vehicles'],
        'total_value': aggregates['total_value'],
        'average_value': aggregates['average_value'],
        'average_model_year': aggregates['average_age'],
        'vehicle_type_distribution': type_distribution,
        'fuel_type_distribution': fuel_distribution,
        'condition_distribution': condition_distribution,
        'age_distribution': age_ranges,
        'value_distribution': value_ranges,
        'vehicle_score_distribution': score_ranges,
    })
