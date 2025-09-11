"""
URL configuration for email_provider app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EmailProviderConfigViewSet,
    EmailProviderHealthLogViewSet,
    EmailProviderUsageLogViewSet,
    EmailProviderTestResultViewSet
)

router = DefaultRouter()
router.register(r'providers', EmailProviderConfigViewSet, basename='email-provider')
router.register(r'health-logs', EmailProviderHealthLogViewSet, basename='email-provider-health-log')
router.register(r'usage-logs', EmailProviderUsageLogViewSet, basename='email-provider-usage-log')
router.register(r'test-results', EmailProviderTestResultViewSet, basename='email-provider-test-result')

urlpatterns = [
    path('', include(router.urls)),
]
