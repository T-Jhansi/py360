from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import (
    WhatsAppBusinessAccount,
    WhatsAppPhoneNumber,
    WhatsAppMessage,
    WhatsAppMessageTemplate,
)


@receiver(pre_save, sender=WhatsAppBusinessAccount)
def whatsapp_business_account_pre_save(sender, instance, **kwargs):
    """Handle pre-save logic for WhatsApp Business Account"""
    
    # Set as default if this is the first account for the user
    if not instance.pk and instance.created_by:
        existing_accounts = WhatsAppBusinessAccount.objects.filter(
            created_by=instance.created_by,
            is_deleted=False
        ).count()
        
        if existing_accounts == 0:
            instance.is_default = True
    
    # Ensure only one default account per user
    if instance.is_default and instance.created_by:
        WhatsAppBusinessAccount.objects.filter(
            created_by=instance.created_by,
            is_deleted=False
        ).exclude(pk=instance.pk).update(is_default=False)


@receiver(post_save, sender=WhatsAppBusinessAccount)
def whatsapp_business_account_post_save(sender, instance, created, **kwargs):
    """Handle post-save logic for WhatsApp Business Account"""
    
    if created:
        # Log account creation
        print(f"Created new WhatsApp Business Account: {instance.name} (WABA ID: {instance.waba_id})")
        
        # Set up default webhook events if not specified
        if not instance.subscribed_webhook_events:
            instance.subscribed_webhook_events = [
                'messages',
                'message_deliveries', 
                'message_reads',
                'message_template_status_update'
            ]
            instance.save(update_fields=['subscribed_webhook_events'])


@receiver(pre_save, sender=WhatsAppPhoneNumber)
def whatsapp_phone_number_pre_save(sender, instance, **kwargs):
    """Handle pre-save logic for WhatsApp Phone Number"""
    
    # Set as primary if this is the first phone number for the WABA
    if not instance.pk and instance.waba_account:
        existing_phone_numbers = WhatsAppPhoneNumber.objects.filter(
            waba_account=instance.waba_account,
            is_active=True
        ).count()
        
        if existing_phone_numbers == 0:
            instance.is_primary = True
            instance.status = 'verified'  # Auto-verify first phone number
    
    # Ensure only one primary phone number per WABA
    if instance.is_primary and instance.waba_account:
        WhatsAppPhoneNumber.objects.filter(
            waba_account=instance.waba_account,
            is_active=True
        ).exclude(pk=instance.pk).update(is_primary=False)


@receiver(post_save, sender=WhatsAppPhoneNumber)
def whatsapp_phone_number_post_save(sender, instance, created, **kwargs):
    """Handle post-save logic for WhatsApp Phone Number"""
    
    if created:
        # Log phone number creation
        print(f"Added phone number {instance.display_phone_number or instance.phone_number} to WABA {instance.waba_account.name}")
        
        # Set verified_at timestamp if status is verified
        if instance.status == 'verified' and not instance.verified_at:
            instance.verified_at = timezone.now()
            instance.save(update_fields=['verified_at'])


@receiver(post_save, sender=WhatsAppMessage)
def whatsapp_message_post_save(sender, instance, created, **kwargs):
    """Handle post-save logic for WhatsApp Message"""
    
    if created:
        # Log message creation
        direction = instance.get_direction_display()
        message_type = instance.get_message_type_display()
        print(f"Created {direction} {message_type} message: {instance.message_id}")
        
        # Update customer communication preferences if customer is linked
        if instance.customer and instance.direction == 'outbound':
            # You can add logic here to update customer communication logs
            # or trigger other customer-related actions
            pass


@receiver(post_save, sender=WhatsAppMessageTemplate)
def whatsapp_message_template_post_save(sender, instance, created, **kwargs):
    """Handle post-save logic for WhatsApp Message Template"""
    
    if created:
        # Log template creation
        print(f"Created message template: {instance.name} for WABA {instance.waba_account.name}")
        
        # Set approved_at timestamp if status is approved
        if instance.status == 'approved' and not instance.approved_at:
            instance.approved_at = timezone.now()
            instance.save(update_fields=['approved_at'])
    
    # Handle status changes
    if not created and 'status' in kwargs.get('update_fields', []):
        if instance.status == 'approved' and not instance.approved_at:
            instance.approved_at = timezone.now()
            instance.save(update_fields=['approved_at'])
            
            # Log template approval
            print(f"Message template approved: {instance.name}")
        
        elif instance.status == 'rejected':
            # Log template rejection
            print(f"Message template rejected: {instance.name} - {instance.rejection_reason}")
