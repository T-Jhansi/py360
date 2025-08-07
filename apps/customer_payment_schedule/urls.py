
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'customer_payment_schedule'

router = DefaultRouter()
router.register(r'', views.CustomerPaymentScheduleViewSet, basename='customer-payment-schedule')

urlpatterns = [
    path('', include(router.urls)),
]
