from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PolicyExclusionViewSet

router = DefaultRouter()
router.register(r'', PolicyExclusionViewSet, basename='policy-exclusions')

urlpatterns = [
    path('', include(router.urls)),
]
