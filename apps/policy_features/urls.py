from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PolicyFeatureViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'policy-features', PolicyFeatureViewSet, basename='policy-features')

urlpatterns = [
    path('api/', include(router.urls)),
]
