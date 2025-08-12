from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PolicyConditionViewSet

router = DefaultRouter()
router.register(r'', PolicyConditionViewSet, basename='policy-conditions')

urlpatterns = [
    path('', include(router.urls)),
]
