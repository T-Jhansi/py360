"""
URL configuration for Customer Assets app.
"""

from django.urls import path
from . import views

app_name = 'customer_assets'

urlpatterns = [
    # List and create customer assets
    path(
        '',
        views.CustomerAssetsListCreateView.as_view(),
        name='customer-assets-list-create'
    ),
    
    # Detail view for customer assets (retrieve, update, delete)
    path(
        '<int:pk>/',
        views.CustomerAssetsDetailView.as_view(),
        name='customer-assets-detail'
    ),
    
    # Get assets by customer ID
    path(
        'customer/<int:customer_id>/',
        views.customer_assets_by_customer,
        name='customer-assets-by-customer'
    ),
    
    # Statistics
    path(
        'statistics/',
        views.customer_assets_statistics,
        name='customer-assets-statistics'
    ),
]
