"""
Signals for customer_communication_preferences app to automatically update last_contact_date in Customer model
"""
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.db import transaction
from django.utils import timezone
from .models import CommunicationLog


@receiver(post_save, sender=CommunicationLog)
def update_last_contact_date_on_save(sender, instance, created, **kwargs):
    """
    Update last_contact_date in Customer model when CommunicationLog is created or updated
    """
    try:
        with transaction.atomic():
            if instance.customer:
                # Get the most recent communication date for this customer
                latest_communication = CommunicationLog.objects.filter(
                    customer=instance.customer,
                    is_deleted=False
                ).order_by('-communication_date').first()
                
                if latest_communication:
                    # Update customer's last_contact_date to the most recent communication
                    instance.customer.last_contact_date = latest_communication.communication_date
                    instance.customer.save(update_fields=['last_contact_date'])
                else:
                    # No communications left, set to None
                    instance.customer.last_contact_date = None
                    instance.customer.save(update_fields=['last_contact_date'])
                    
    except Exception as e:
        # Log the error but don't fail the communication log creation
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error updating last_contact_date for customer {instance.customer.id}: {str(e)}")


@receiver(post_delete, sender=CommunicationLog)
def update_last_contact_date_on_delete(sender, instance, **kwargs):
    """
    Update last_contact_date in Customer model when CommunicationLog is deleted
    """
    try:
        with transaction.atomic():
            if instance.customer:
                # Check if there are any other communication logs for this customer
                remaining_communications = CommunicationLog.objects.filter(
                    customer=instance.customer,
                    is_deleted=False
                ).exclude(id=instance.id)
                
                if remaining_communications.exists():
                    # Get the most recent remaining communication
                    latest_communication = remaining_communications.order_by('-communication_date').first()
                    instance.customer.last_contact_date = latest_communication.communication_date
                else:
                    # No communications left, set to None
                    instance.customer.last_contact_date = None
                
                instance.customer.save(update_fields=['last_contact_date'])
                
    except Exception as e:
        # Log the error but don't fail the communication log deletion
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error updating last_contact_date after communication deletion {instance.id}: {str(e)}")


@receiver(pre_save, sender=CommunicationLog)
def update_last_contact_date_on_soft_delete(sender, instance, **kwargs):
    """
    Update last_contact_date in Customer model when CommunicationLog is soft-deleted
    """
    try:
        # Check if this is a soft delete (is_deleted changing from False to True)
        if instance.pk and instance.is_deleted:
            # Get the original instance from database
            try:
                original = CommunicationLog.objects.get(pk=instance.pk)
                if not original.is_deleted and instance.is_deleted:
                    # This is a soft delete
                    with transaction.atomic():
                        if instance.customer:
                            # Check if there are any other non-deleted communications for this customer
                            remaining_communications = CommunicationLog.objects.filter(
                                customer=instance.customer,
                                is_deleted=False
                            ).exclude(id=instance.id)
                            
                            if remaining_communications.exists():
                                # Get the most recent remaining communication
                                latest_communication = remaining_communications.order_by('-communication_date').first()
                                instance.customer.last_contact_date = latest_communication.communication_date
                            else:
                                # No communications left, set to None
                                instance.customer.last_contact_date = None
                            
                            instance.customer.save(update_fields=['last_contact_date'])
                            
            except CommunicationLog.DoesNotExist:
                # Instance doesn't exist in database, skip
                pass
                
    except Exception as e:
        # Log the error but don't fail the communication log update
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error updating last_contact_date after soft delete {instance.id}: {str(e)}")
