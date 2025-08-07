"""
URL configuration for Customer Vehicle app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'customer_vehicle'

# Create router for ViewSet
router = DefaultRouter()
router.register(r'', views.CustomerVehicleViewSet, basename='customer-vehicle')

urlpatterns = [
    # Include ViewSet URLs (provides list and create functionality)
    path('', include(router.urls)),
]
