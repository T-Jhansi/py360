"""
URL configuration for Customer Payments app.
"""

from django.urls import path
from . import views

app_name = 'customer_payments'

urlpatterns = [
    # List and create customer payments
    path(
        '',
        views.CustomerPaymentListCreateView.as_view(),
        name='customer-payment-list-create'
    ),
    
    # Detail view for customer payment (retrieve, update, delete)
    path(
        '<int:pk>/',
        views.CustomerPaymentDetailView.as_view(),
        name='customer-payment-detail'
    ),
    
    # Get payments by renewal case ID
    path(
        'renewal-case/<int:renewal_case_id>/',
        views.customer_payments_by_renewal_case,
        name='customer-payments-by-renewal-case'
    ),
    
    # Get payments by customer ID
    path(
        'customer/<int:customer_id>/',
        views.customer_payments_by_customer,
        name='customer-payments-by-customer'
    ),
    
    # Process payment refund
    path(
        '<int:payment_id>/refund/',
        views.process_payment_refund,
        name='process-payment-refund'
    ),
    
    # Update payment status
    path(
        '<int:payment_id>/status/',
        views.update_payment_status,
        name='update-payment-status'
    ),
    
    # Statistics
    path(
        'statistics/',
        views.payment_statistics,
        name='payment-statistics'
    ),
    
    # Summary for analytics
    path(
        'summary/',
        views.payment_summary,
        name='payment-summary'
    ),
]
