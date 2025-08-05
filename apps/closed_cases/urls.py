from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClosedCasesViewSet

router = DefaultRouter()
router.register(r'closed-cases', ClosedCasesViewSet, basename='closed-cases')

app_name = 'closed_cases'

urlpatterns = [
    path('', include(router.urls)),
]
