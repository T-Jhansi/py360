from django.db import models
from django.conf import settings

# RenewalTimeline model removed - using CommonRenewalTimelineSettings instead


class CommonRenewalTimelineSettings(models.Model):
    """
    Common renewal timeline settings that apply to all customers
    These are global settings, not customer-specific
    """
    # Core preferences - common for all customers
    renewal_pattern = models.CharField(
        max_length=100, 
        help_text="e.g., 'Pays 7–14 days before due date'",
        default="Pays 7-14 days before due date"
    )
    reminder_days = models.JSONField(
        help_text="Days before due date to send reminders, e.g. [-30, -14, -7]",
        default=list
    )
    reminder_schedule = models.JSONField(
        help_text="Formatted reminder schedule for frontend display",
        default=list,
        blank=True
    )
    auto_renewal_enabled = models.BooleanField(default=False)
    
    # Settings metadata
    is_active = models.BooleanField(default=True)
    description = models.TextField(
        blank=True, 
        null=True,
        help_text="Description of these timeline settings"
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_common_timeline_settings"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_common_timeline_settings"
    )

    class Meta:
        db_table = "common_renewal_timeline_settings"
        verbose_name = "Common Renewal Timeline Settings"
        verbose_name_plural = "Common Renewal Timeline Settings"

    def __str__(self):
        return f"Common Timeline Settings - {self.renewal_pattern}"