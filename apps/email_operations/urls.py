from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EmailMessageViewSet,
    EmailQueueViewSet,
    EmailTrackingViewSet,
    EmailDeliveryReportViewSet,
    EmailAnalyticsViewSet
)

router = DefaultRouter()
router.register(r'messages', EmailMessageViewSet, basename='email-message')
router.register(r'queue', EmailQueueViewSet, basename='email-queue')
router.register(r'tracking', EmailTrackingViewSet, basename='email-tracking')
router.register(r'delivery-reports', EmailDeliveryReportViewSet, basename='email-delivery-report')
router.register(r'analytics', EmailAnalyticsViewSet, basename='email-analytics')

urlpatterns = [
    path('', include(router.urls)),
]
