from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Policy


@receiver(post_save, sender=Policy)
def update_customer_metrics_on_policy_save(sender, instance, created, **kwargs):
    """Update customer metrics when a policy is created or updated"""
    if instance.customer:
        instance.customer.update_metrics()


@receiver(post_delete, sender=Policy)
def update_customer_metrics_on_policy_delete(sender, instance, **kwargs):
    """Update customer metrics when a policy is deleted"""
    if instance.customer:
        instance.customer.update_metrics()
