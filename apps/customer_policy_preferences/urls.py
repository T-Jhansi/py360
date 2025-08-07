"""
URL configuration for Customer Policy Preferences app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'customer_policy_preferences'

# Create router for ViewSet
router = DefaultRouter()
router.register(r'', views.CustomerPolicyPreferenceViewSet, basename='customer-policy-preference')

urlpatterns = [
    # Include ViewSet URLs
    path('', include(router.urls)),
]
