from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'customer_financial_profile'

router = DefaultRouter()
router.register(r'', views.CustomerFinancialProfileViewSet, basename='customer-financial-profile')

urlpatterns = [
    path('', include(router.urls)),
]
