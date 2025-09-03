from django.db import models
from django.conf import settings
from apps.customers.models import Customer
from apps.policies.models import Policy
from apps.renewals.models import RenewalCase
from apps.channels.models import Channel
from apps.customer_payments.models import CustomerPayment

class RenewalTimeline(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="renewal_timelines"
    )
    policy = models.ForeignKey(
        Policy, on_delete=models.CASCADE, related_name="renewal_timelines"
    )
    renewal_case = models.ForeignKey(
        RenewalCase, on_delete=models.SET_NULL, null=True, blank=True, related_name="renewal_timelines"
    )
    preferred_channel = models.ForeignKey(
        Channel, on_delete=models.SET_NULL, null=True, blank=True, related_name="renewal_timelines"
    )
    last_payment = models.ForeignKey(
        CustomerPayment, on_delete=models.SET_NULL, null=True, blank=True, related_name="renewal_timelines"
    )

    # Core preferences
    renewal_pattern = models.CharField(max_length=100, help_text="e.g., 'Pays 7–14 days before due date'")
    reminder_days = models.JSONField(help_text="Days before due date to send reminders, e.g. [-30, -14, -7]")
    next_due_date = models.DateField(null=True, blank=True)
    auto_renewal_enabled = models.BooleanField(default=False)

    # Tracking
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_renewal_timelines"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_renewal_timelines"
    )

    class Meta:
        db_table = "renewal_timelines"
        verbose_name = "Renewal Timeline"
        verbose_name_plural = "Renewal Timelines"
        unique_together = ("customer", "policy")

    def __str__(self):
        return f"{self.customer} - {self.policy} Timeline"
