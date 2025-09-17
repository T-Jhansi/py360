"""
Customer Installment Integration Signals
This module provides Django signals for automatically creating installments
when policies are created and linking payments to installments.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .services import InstallmentIntegrationService


@receiver(post_save, sender='policies.Policy')
def create_installments_on_policy_creation(sender, instance, created, **kwargs):
    """
    Automatically create installments when a new policy is created
    This signal is triggered after a Policy is saved
    """
    if created:  # Only for new policies, not updates
        try:
            # Get or create renewal case for this policy
            renewal_case = None
            if hasattr(instance, 'renewal_cases'):
                renewal_case = instance.renewal_cases.first()
            
            # Create installments for the policy
            result = InstallmentIntegrationService.create_installments_for_policy(
                instance, renewal_case
            )
            
            if result['success']:
                print(f"✅ Created {result['installments_created']} installments for policy {instance.policy_number}")
            else:
                print(f"❌ Failed to create installments for policy {instance.policy_number}: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Error in create_installments_on_policy_creation: {str(e)}")


@receiver(post_save, sender='customer_payments.CustomerPayment')
def link_payment_to_installment(sender, instance, created, **kwargs):
    """
    Automatically link payments to installments when a payment is created
    This signal is triggered after a CustomerPayment is saved
    """
    if created:  # Only for new payments, not updates
        try:
            # Only link if payment is successful
            if instance.payment_status == 'completed':
                result = InstallmentIntegrationService.link_payment_to_installment(instance)
                
                if result['success']:
                    print(f"✅ Payment {instance.transaction_id} linked to installment {result.get('installment_id')}")
                else:
                    print(f"⚠️ Could not link payment {instance.transaction_id}: {result.get('message', 'Unknown error')}")
                    
        except Exception as e:
            print(f"❌ Error in link_payment_to_installment: {str(e)}")


@receiver(post_save, sender='renewals.RenewalCase')
def create_installments_on_renewal_case_creation(sender, instance, created, **kwargs):
    """
    Create installments when a renewal case is created
    This can be used for renewal-specific installment creation
    """
    if created:  # Only for new renewal cases
        try:
            # Check if this renewal case has a policy
            if hasattr(instance, 'policy') and instance.policy:
                # Create installments for the renewal
                result = InstallmentIntegrationService.create_installments_for_policy(
                    instance.policy, instance
                )
                
                if result['success']:
                    print(f"✅ Created {result['installments_created']} installments for renewal case {instance.case_number}")
                else:
                    print(f"❌ Failed to create installments for renewal case {instance.case_number}: {result.get('error', 'Unknown error')}")
                    
        except Exception as e:
            print(f"❌ Error in create_installments_on_renewal_case_creation: {str(e)}")
