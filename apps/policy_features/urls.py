from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PolicyFeatureViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'', PolicyFeatureViewSet, basename='policy-features')

urlpatterns = [
    path('', include(router.urls)),
]
