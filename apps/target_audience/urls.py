from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TargetAudienceViewSet

router = DefaultRouter()
router.register(r'audiences', TargetAudienceViewSet, basename='target-audience')

urlpatterns = [
    path('', include(router.urls)),
]
