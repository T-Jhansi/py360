"""
Policy Timeline models for the Intelipro Insurance Policy Renewal System.
"""

from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import BaseModel
from apps.customers.models import Customer
from apps.policies.models import Policy

User = get_user_model()


class PolicyTimeline(BaseModel):
    """
    Policy Timeline model to track all policy events, communications, and changes
    """
    
    EVENT_TYPE_CHOICES = [
        ('communication', 'Communication'),
        ('creation', 'Policy Creation'),
        ('renewal', 'Policy Renewal'),
        ('modification', 'Policy Modification'),
        ('claim', 'Claim Event'),
        ('payment', 'Payment Event'),
        ('coverage_review', 'Coverage Review'),
        ('agent_interaction', 'Agent Interaction'),
    ]
    
    EVENT_STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('pending', 'Pending'),
        ('scheduled', 'Scheduled'),
        ('cancelled', 'Cancelled'),
        ('in_progress', 'In Progress'),
    ]
    
    # Core Foreign Keys
    policy = models.ForeignKey(
        Policy, 
        on_delete=models.CASCADE, 
        related_name='timeline_events',
        help_text="Related policy"
    )
    customer = models.ForeignKey(
        Customer, 
        on_delete=models.CASCADE, 
        related_name='policy_timeline_events',
        help_text="Related customer"
    )
    agent = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='policy_timeline_events',
        help_text="Assigned agent for this event"
    )
    
    # Event Information
    event_type = models.CharField(
        max_length=20, 
        choices=EVENT_TYPE_CHOICES,
        db_index=True,
        help_text="Type of timeline event"
    )
    event_title = models.CharField(
        max_length=200,
        help_text="Title of the event (e.g., 'Policy Renewed', 'Coverage Review')"
    )
    event_description = models.TextField(
        help_text="Detailed description of the event"
    )
    event_date = models.DateTimeField(
        db_index=True,
        help_text="When the event occurred"
    )
    event_status = models.CharField(
        max_length=20, 
        choices=EVENT_STATUS_CHOICES, 
        default='completed',
        help_text="Current status of the event"
    )
    
    # Financial Fields
    premium_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Premium amount at time of event"
    )
    coverage_details = models.TextField(
        blank=True,
        help_text="Coverage details at time of event"
    )
    discount_info = models.CharField(
        max_length=200, 
        blank=True,
        help_text="Discount information (e.g., '5% multi-policy discount applied')"
    )
    
    # Outcome Fields
    outcome = models.TextField(
        blank=True,
        help_text="Outcome or result of the event"
    )
    follow_up_required = models.BooleanField(
        default=False,
        help_text="Whether follow-up is required"
    )
    follow_up_date = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Date for follow-up action"
    )
    
    # Display Fields
    display_icon = models.CharField(
        max_length=50, 
        blank=True,
        help_text="Icon identifier for timeline UI display"
    )
    is_milestone = models.BooleanField(
        default=False,
        help_text="Mark as important milestone event"
    )
    sequence_order = models.IntegerField(
        default=0,
        help_text="Order for displaying events in timeline"
    )
    
    class Meta:
        db_table = 'policy_timeline'
        ordering = ['-event_date', '-sequence_order']
        indexes = [
            models.Index(fields=['policy', 'event_date']),
            models.Index(fields=['customer', 'event_date']),
            models.Index(fields=['event_type', 'event_date']),
            models.Index(fields=['agent', 'event_date']),
            models.Index(fields=['event_status']),
            models.Index(fields=['is_milestone']),
        ]
    
    def __str__(self):
        return f"{self.event_title} - {self.policy.policy_number} ({self.event_date.strftime('%Y-%m-%d')})"
    
    @property
    def formatted_event_date(self):
        """Return formatted date for display"""
        return self.event_date.strftime('%b %d, %Y')
    
    @property
    def event_category_display(self):
        """Return display name for event type"""
        return dict(self.EVENT_TYPE_CHOICES).get(self.event_type, self.event_type)
