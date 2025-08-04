"""
URL configuration for Hierarchy Management API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HierarchyManagementViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'units', HierarchyManagementViewSet, basename='hierarchy-units')

app_name = 'hierarchy'

urlpatterns = [
    path('api/', include(router.urls)),
]
