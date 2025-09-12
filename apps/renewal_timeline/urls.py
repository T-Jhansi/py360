from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CommonRenewalTimelineSettingsViewSet

router = DefaultRouter()
router.register(r'renewal-timelines', CommonRenewalTimelineSettingsViewSet, basename='common-renewal-timeline')

app_name = 'renewal_timeline'

urlpatterns = [
    path('', include(router.urls)),
]


