from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'customer_communication_preferences'

router = DefaultRouter()
router.register(r'preferences', views.CustomerCommunicationPreferenceViewSet, basename='communication-preferences')

urlpatterns = [
    path('', include(router.urls)),
]
