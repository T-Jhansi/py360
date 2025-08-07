"""
URL configuration for Customer Payment Schedule app.
"""

from django.urls import path
from . import views

app_name = 'customer_payment_schedule'

urlpatterns = [
    # List and create payment schedules
    path(
        '',
        views.PaymentScheduleListCreateView.as_view(),
        name='payment-schedule-list-create'
    ),
    
    # Detail view for payment schedule (retrieve, update, delete)
    path(
        '<int:pk>/',
        views.PaymentScheduleDetailView.as_view(),
        name='payment-schedule-detail'
    ),
    
    # Get schedules by renewal case ID
    path(
        'renewal-case/<int:renewal_case_id>/',
        views.payment_schedules_by_renewal_case,
        name='payment-schedules-by-renewal-case'
    ),
    
    # Get schedules by customer ID
    path(
        'customer/<int:customer_id>/',
        views.payment_schedules_by_customer,
        name='payment-schedules-by-customer'
    ),
    
    # Process scheduled payment
    path(
        '<int:schedule_id>/process/',
        views.process_scheduled_payment,
        name='process-scheduled-payment'
    ),
    
    # Reschedule payment
    path(
        '<int:schedule_id>/reschedule/',
        views.reschedule_payment,
        name='reschedule-payment'
    ),
    
    # Mark payment as failed
    path(
        '<int:schedule_id>/mark-failed/',
        views.mark_payment_failed,
        name='mark-payment-failed'
    ),
    
    # Setup auto payment
    path(
        '<int:schedule_id>/auto-payment/',
        views.setup_auto_payment,
        name='setup-auto-payment'
    ),
    
    # Send payment reminder
    path(
        '<int:schedule_id>/send-reminder/',
        views.send_payment_reminder,
        name='send-payment-reminder'
    ),
    
    # Notify customer
    path(
        '<int:schedule_id>/notify-customer/',
        views.notify_customer,
        name='notify-customer'
    ),
    
    # Create bulk schedules
    path(
        'bulk-create/',
        views.create_bulk_schedules,
        name='create-bulk-schedules'
    ),
    
    # Statistics
    path(
        'statistics/',
        views.payment_schedule_statistics,
        name='payment-schedule-statistics'
    ),
    
    # Summary for analytics
    path(
        'summary/',
        views.payment_schedule_summary,
        name='payment-schedule-summary'
    ),
]
