"""
URLs for Outstanding Amounts functionality
"""

from django.urls import path
from .views import (
    get_outstanding_summary_api,
    initiate_payment_api,
    setup_payment_plan_api
)

app_name = 'outstanding_amounts'

urlpatterns = [
    # Outstanding amounts summary
    path(
        'cases/<str:case_id>/outstanding-amounts/summary/',
        get_outstanding_summary_api,
        name='get-outstanding-summary'
    ),
    
    # Initiate payment for outstanding amounts
    path(
        'cases/<str:case_id>/outstanding-amounts/pay/',
        initiate_payment_api,
        name='initiate-payment'
    ),
    
    # Setup payment plan for outstanding amounts
    path(
        'cases/<str:case_id>/outstanding-amounts/setup-payment-plan/',
        setup_payment_plan_api,
        name='setup-payment-plan'
    ),
]
