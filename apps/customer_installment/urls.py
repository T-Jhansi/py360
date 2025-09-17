from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomerInstallmentViewSet

router = DefaultRouter()
router.register(r'', CustomerInstallmentViewSet, basename='customer-installment')

urlpatterns = [
    path('', include(router.urls)),
]
