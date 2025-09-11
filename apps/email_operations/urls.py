"""
URL configuration for email_operations app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EmailMessageViewSet,
    EmailQueueViewSet,
    EmailTrackingViewSet,
    EmailDeliveryReportViewSet,
    EmailAnalyticsViewSet,
    track_email_open,
    track_email_click
)

router = DefaultRouter()
router.register(r'messages', EmailMessageViewSet, basename='email-message')
router.register(r'queues', EmailQueueViewSet, basename='email-queue')
router.register(r'tracking', EmailTrackingViewSet, basename='email-tracking')
router.register(r'delivery-reports', EmailDeliveryReportViewSet, basename='email-delivery-report')
router.register(r'analytics', EmailAnalyticsViewSet, basename='email-analytics')

urlpatterns = [
    path('', include(router.urls)),
    
    # Public tracking endpoints (no authentication required)
    path('track/open/<uuid:message_id>/', track_email_open, name='track-email-open'),
    path('track/click/<uuid:message_id>/', track_email_click, name='track-email-click'),
]
