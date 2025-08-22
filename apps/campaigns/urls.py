from .views import (
    CampaignViewSet, EmailTrackingView, EmailClickTrackingView,
    get_all_campaigns, test_tracking_pixel, get_campaign_tracking_stats
)
from rest_framework.routers import DefaultRouter
from django.urls import path, include

router = DefaultRouter()
router.register(r'', CampaignViewSet, basename='campaign')

urlpatterns = [
    path('track-open/', EmailTrackingView.as_view(), name='track-email-open'),
    path('track-click/', EmailClickTrackingView.as_view(), name='track-email-click'),
    path('test-tracking/', test_tracking_pixel, name='test-tracking-pixel'),
    path('<int:campaign_id>/tracking-stats/', get_campaign_tracking_stats, name='campaign-tracking-stats'),
    path('list/', get_all_campaigns, name='get-all-campaigns'),
    path('', include(router.urls)),
]
