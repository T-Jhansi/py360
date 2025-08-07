"""
URL configuration for Customer Vehicle app.
"""

from django.urls import path
from . import views

app_name = 'customer_vehicle'

urlpatterns = [
    # List and create customer vehicles
    path(
        '',
        views.CustomerVehicleListCreateView.as_view(),
        name='customer-vehicle-list-create'
    ),
    
    # Detail view for customer vehicle (retrieve, update, delete)
    path(
        '<int:pk>/',
        views.CustomerVehicleDetailView.as_view(),
        name='customer-vehicle-detail'
    ),
    
    # Get vehicles by customer assets ID
    path(
        'customer-assets/<int:customer_assets_id>/',
        views.customer_vehicles_by_customer_assets,
        name='customer-vehicles-by-assets'
    ),
    
    # Get vehicles by customer ID
    path(
        'customer/<int:customer_id>/',
        views.customer_vehicles_by_customer,
        name='customer-vehicles-by-customer'
    ),
    
    # Statistics
    path(
        'statistics/',
        views.customer_vehicle_statistics,
        name='customer-vehicle-statistics'
    ),
]
