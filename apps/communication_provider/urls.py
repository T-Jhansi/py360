from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CommunicationProviderViewSet

router = DefaultRouter()
router.register(r'providers', CommunicationProviderViewSet, basename='communication-provider')

urlpatterns = [
    path('', include(router.urls)),
]
