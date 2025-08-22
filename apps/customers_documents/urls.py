from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomerDocumentViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'customer-documents', CustomerDocumentViewSet, basename='customer-documents')

urlpatterns = [
    path('api/', include(router.urls)),
]
