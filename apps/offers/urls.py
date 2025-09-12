from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OfferViewSet

router = DefaultRouter()
router.register(r'offers', OfferViewSet, basename='offer')

app_name = 'offers'

urlpatterns = [
    path('', include(router.urls)),
]
