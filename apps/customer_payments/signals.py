"""
Signals for customer_payments app to automatically update payment_status in related models
"""
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.db import transaction
from .models import CustomerPayment


@receiver(post_save, sender=CustomerPayment)
def update_payment_status_on_save(sender, instance, created, **kwargs):
    """
    Update payment_status in related RenewalCase when CustomerPayment is created or updated
    """
    try:
        with transaction.atomic():
            # Map CustomerPayment status to RenewalCase payment_status
            status_mapping = {
                'completed': 'success',
                'failed': 'failed',
                'cancelled': 'failed',
                'refunded': 'failed',
                'pending': 'pending',
                'processing': 'pending',
                'partial': 'success',  # Partial payment is still considered success
                'overdue': 'failed',
            }
            
            # Get the mapped status
            renewal_payment_status = status_mapping.get(instance.payment_status, 'pending')
            
            # Update related RenewalCase if it exists
            if instance.renewal_case:
                instance.renewal_case.payment_status = renewal_payment_status
                instance.renewal_case.save(update_fields=['payment_status'])
                
            # Update related Customer if it exists
            if instance.customer:
                # Update customer's payment status based on latest payment
                latest_payment = CustomerPayment.objects.filter(
                    customer=instance.customer,
                    is_deleted=False
                ).order_by('-payment_date').first()
                
                if latest_payment:
                    customer_payment_status = status_mapping.get(latest_payment.payment_status, 'pending')
                    # You can add a payment_status field to Customer model if needed
                    # instance.customer.payment_status = customer_payment_status
                    # instance.customer.save(update_fields=['payment_status'])
                    
    except Exception as e:
        # Log the error but don't fail the payment creation
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error updating payment status for payment {instance.id}: {str(e)}")


@receiver(post_delete, sender=CustomerPayment)
def update_payment_status_on_delete(sender, instance, **kwargs):
    """
    Update payment_status in related RenewalCase when CustomerPayment is deleted
    """
    try:
        with transaction.atomic():
            # Update related RenewalCase if it exists
            if instance.renewal_case:
                # Check if there are any other payments for this renewal case
                remaining_payments = CustomerPayment.objects.filter(
                    renewal_case=instance.renewal_case,
                    is_deleted=False
                ).exclude(id=instance.id)
                
                if remaining_payments.exists():
                    # Get the latest remaining payment
                    latest_payment = remaining_payments.order_by('-payment_date').first()
                    status_mapping = {
                        'completed': 'success',
                        'failed': 'failed',
                        'cancelled': 'failed',
                        'refunded': 'failed',
                        'pending': 'pending',
                        'processing': 'pending',
                        'partial': 'success',
                        'overdue': 'failed',
                    }
                    renewal_payment_status = status_mapping.get(latest_payment.payment_status, 'pending')
                else:
                    # No payments left, set to pending
                    renewal_payment_status = 'pending'
                
                instance.renewal_case.payment_status = renewal_payment_status
                instance.renewal_case.save(update_fields=['payment_status'])
                
    except Exception as e:
        # Log the error but don't fail the payment deletion
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error updating payment status after payment deletion {instance.id}: {str(e)}")


@receiver(pre_save, sender=CustomerPayment)
def update_payment_status_on_soft_delete(sender, instance, **kwargs):
    """
    Update payment_status in related RenewalCase when CustomerPayment is soft-deleted
    """
    try:
        # Check if this is a soft delete (is_deleted changing from False to True)
        if instance.pk and instance.is_deleted:
            # Get the original instance from database
            try:
                original = CustomerPayment.objects.get(pk=instance.pk)
                if not original.is_deleted and instance.is_deleted:
                    # This is a soft delete
                    with transaction.atomic():
                        if instance.renewal_case:
                            # Check if there are any other non-deleted payments for this renewal case
                            remaining_payments = CustomerPayment.objects.filter(
                                renewal_case=instance.renewal_case,
                                is_deleted=False
                            ).exclude(id=instance.id)
                            
                            if remaining_payments.exists():
                                # Get the latest remaining payment
                                latest_payment = remaining_payments.order_by('-payment_date').first()
                                status_mapping = {
                                    'completed': 'success',
                                    'failed': 'failed',
                                    'cancelled': 'failed',
                                    'refunded': 'failed',
                                    'pending': 'pending',
                                    'processing': 'pending',
                                    'partial': 'success',
                                    'overdue': 'failed',
                                }
                                renewal_payment_status = status_mapping.get(latest_payment.payment_status, 'pending')
                            else:
                                # No payments left, set to pending
                                renewal_payment_status = 'pending'
                            
                            instance.renewal_case.payment_status = renewal_payment_status
                            instance.renewal_case.save(update_fields=['payment_status'])
                            
            except CustomerPayment.DoesNotExist:
                # Instance doesn't exist in database, skip
                pass
                
    except Exception as e:
        # Log the error but don't fail the payment update
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error updating payment status after soft delete {instance.id}: {str(e)}")
