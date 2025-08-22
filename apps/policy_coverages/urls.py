from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PolicyCoverageViewSet

router = DefaultRouter()
router.register(r'', PolicyCoverageViewSet, basename='policy-coverages')

urlpatterns = [
    path('', include(router.urls)),
]
