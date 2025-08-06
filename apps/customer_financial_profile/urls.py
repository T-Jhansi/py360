from django.urls import path
from . import views

app_name = 'customer_financial_profile'

urlpatterns = [
    # List and create financial profiles
    path(
        '',
        views.CustomerFinancialProfileListCreateView.as_view(),
        name='financial-profile-list-create'
    ),
    
    # Detail view for financial profile (retrieve, update, delete)
    path(
        '<int:pk>/',
        views.CustomerFinancialProfileDetailView.as_view(),
        name='financial-profile-detail'
    ),
    
    # Get financial profile by customer ID
    path(
        'customer/<int:customer_id>/',
        views.customer_financial_profile_by_customer,
        name='financial-profile-by-customer'
    ),
    
    # Update capacity utilization
    path(
        '<int:pk>/update-capacity/',
        views.update_capacity_utilization,
        name='update-capacity-utilization'
    ),
    
    # Statistics
    path(
        'statistics/',
        views.financial_profile_statistics,
        name='financial-profile-statistics'
    ),
]
