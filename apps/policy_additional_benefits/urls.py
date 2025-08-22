from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PolicyAdditionalBenefitViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'', PolicyAdditionalBenefitViewSet, basename='policy-additional-benefits')

urlpatterns = [
    path('', include(router.urls)),
]
