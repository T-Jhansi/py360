"""
URL configuration for Customer Policy Preferences app.
"""

from django.urls import path
from . import views

app_name = 'customer_policy_preferences'

urlpatterns = [
    # List and create customer policy preferences
    path(
        '',
        views.CustomerPolicyPreferenceListCreateView.as_view(),
        name='customer-policy-preference-list-create'
    ),
    
    # Detail view for customer policy preference (retrieve, update, delete)
    path(
        '<int:pk>/',
        views.CustomerPolicyPreferenceDetailView.as_view(),
        name='customer-policy-preference-detail'
    ),
    
    # Get preferences by customer ID
    path(
        'customer/<int:customer_id>/',
        views.customer_preferences_by_customer,
        name='customer-preferences-by-customer'
    ),
    
    # Get preferences by renewal case ID
    path(
        'renewal-case/<int:renewal_case_id>/',
        views.customer_preferences_by_renewal_case,
        name='customer-preferences-by-renewal-case'
    ),
    
    # Statistics
    path(
        'statistics/',
        views.customer_preference_statistics,
        name='customer-preference-statistics'
    ),
    
    # Summary for analytics
    path(
        'summary/',
        views.customer_preference_summary,
        name='customer-preference-summary'
    ),
]
