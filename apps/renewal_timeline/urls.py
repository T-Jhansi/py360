from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RenewalTimelineViewSet

router = DefaultRouter()
router.register(r'renewal-timelines', RenewalTimelineViewSet, basename='renewal-timeline')

app_name = 'renewal_timeline'

urlpatterns = [
    path('', include(router.urls)),
]


