# campaigns/urls.py

from .views import (
    CampaignViewSet, EmailTrackingView, EmailClickTrackingView,
    get_all_campaigns, test_tracking_pixel, get_campaign_tracking_stats
)
from rest_framework.routers import DefaultRouter
from django.urls import path, include

router = DefaultRouter()
router.register(r'', CampaignViewSet, basename='campaign')

urlpatterns = [
    # Email tracking endpoints (no authentication required) - MUST BE FIRST
    path('track-open/', EmailTrackingView.as_view(), name='track-email-open'),
    path('track-click/', EmailClickTrackingView.as_view(), name='track-email-click'),

    # Test tracking endpoint
    path('test-tracking/', test_tracking_pixel, name='test-tracking-pixel'),

    # Campaign tracking stats
    path('<int:campaign_id>/tracking-stats/', get_campaign_tracking_stats, name='campaign-tracking-stats'),

    # API endpoints
    path('list/', get_all_campaigns, name='get-all-campaigns'),

    # Router URLs (MUST BE LAST)
    path('', include(router.urls)),
]
