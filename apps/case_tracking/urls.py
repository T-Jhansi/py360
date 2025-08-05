from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CaseTrackingViewSet

router = DefaultRouter()
router.register(r'cases', CaseTrackingViewSet, basename='case-tracking')

app_name = 'case_tracking'

urlpatterns = [
    path('', include(router.urls)),
]
