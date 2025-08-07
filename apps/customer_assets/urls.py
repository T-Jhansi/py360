from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'customer_assets'

router = DefaultRouter()
router.register(r'assets', views.CustomerAssetsViewSet, basename='customer-asset')

urlpatterns = [
    path('', include(router.urls)),
]
