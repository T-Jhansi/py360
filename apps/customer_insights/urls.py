"""
URL configuration for Customer Insights app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomerInsightsViewSet, CustomerInsightsAPIView

# Create router for ViewSet
router = DefaultRouter()
router.register(r'insights', CustomerInsightsViewSet, basename='customer-insights')

app_name = 'customer_insights'

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Standalone API endpoints
    path('customer/<int:customer_id>/insights/', CustomerInsightsAPIView.as_view(), name='customer-insights-detail'),
    
    # Additional specific endpoints
    path('customer/<int:customer_id>/insights/payment/', 
         CustomerInsightsViewSet.as_view({'get': 'get_payment_insights'}), 
         name='customer-payment-insights'),
    
    path('customer/<int:customer_id>/insights/communication/', 
         CustomerInsightsViewSet.as_view({'get': 'get_communication_insights'}), 
         name='customer-communication-insights'),
    
    path('customer/<int:customer_id>/insights/claims/', 
         CustomerInsightsViewSet.as_view({'get': 'get_claims_insights'}), 
         name='customer-claims-insights'),
    
    path('customer/<int:customer_id>/payment-schedule/', 
         CustomerInsightsViewSet.as_view({'get': 'get_payment_schedule'}), 
         name='customer-payment-schedule'),
    
    path('customer/<int:customer_id>/payment-history/', 
         CustomerInsightsViewSet.as_view({'get': 'get_payment_history'}), 
         name='customer-payment-history'),
    
    path('customer/<int:customer_id>/communication-history/', 
         CustomerInsightsViewSet.as_view({'get': 'get_communication_history'}), 
         name='customer-communication-history'),
    
    path('customer/<int:customer_id>/claims-history/', 
         CustomerInsightsViewSet.as_view({'get': 'get_claims_history'}), 
         name='customer-claims-history'),
    
    # Dashboard and summary endpoints
    path('dashboard/', 
         CustomerInsightsViewSet.as_view({'get': 'get_insights_dashboard'}), 
         name='insights-dashboard'),
    
    path('summary/', 
         CustomerInsightsViewSet.as_view({'get': 'get_insights_summary'}), 
         name='insights-summary'),
    
    # Bulk operations
    path('bulk-update/', 
         CustomerInsightsViewSet.as_view({'post': 'bulk_update_insights'}), 
         name='bulk-update-insights'),
]
