"""
URL configuration for Other Insurance Policies app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'other_insurance_policies'

router = DefaultRouter()
router.register(r'', views.OtherInsurancePolicyViewSet, basename='other-insurance-policy')

urlpatterns = [
    path('', include(router.urls)),
]
