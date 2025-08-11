from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PolicyCoverageViewSet

router = DefaultRouter()
router.register(r'policy-coverages', PolicyCoverageViewSet, basename='policy-coverages')

urlpatterns = [
    path('api/', include(router.urls)),
]
