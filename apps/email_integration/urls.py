"""
Email Integration URL Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    EmailWebhookViewSet, EmailAutomationViewSet, EmailAnalyticsViewSet,
    EmailIntegrationViewSet, EmailSLAViewSet, EmailTemplateVariableViewSet,
    EmailAdvancedFeaturesViewSet
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'webhooks', EmailWebhookViewSet, basename='email-webhook')
router.register(r'automations', EmailAutomationViewSet, basename='email-automation')
router.register(r'analytics', EmailAnalyticsViewSet, basename='email-analytics')
router.register(r'integrations', EmailIntegrationViewSet, basename='email-integration')
router.register(r'slas', EmailSLAViewSet, basename='email-sla')
router.register(r'template-variables', EmailTemplateVariableViewSet, basename='email-template-variable')
router.register(r'advanced-features', EmailAdvancedFeaturesViewSet, basename='email-advanced-features')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Additional webhook endpoints
    path('webhooks/sendgrid/', EmailWebhookViewSet.as_view({'post': 'receive_sendgrid'}), name='webhook-sendgrid'),
    path('webhooks/aws-ses/', EmailWebhookViewSet.as_view({'post': 'receive_aws_ses'}), name='webhook-aws-ses'),
]
