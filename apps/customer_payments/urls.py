"""
URL configuration for Customer Payments app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'customer_payments'

# Create router for ViewSet
router = DefaultRouter()
router.register(r'payments', views.CustomerPaymentViewSet, basename='customer-payment')

urlpatterns = [

    path('', include(router.urls)),
]
