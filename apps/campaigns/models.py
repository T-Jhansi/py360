from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import BaseModel, TimestampedModel
from apps.customers.models import Customer
from apps.policies.models import Policy
import uuid
import json

User = get_user_model()

class CampaignType(BaseModel):
    """Types of campaigns (Renewal, Welcome, Follow-up, etc.)"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    default_channels = models.JSONField(default=list, help_text="Default communication channels for this campaign type")
    
    class Meta:
        db_table = 'campaign_types'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Campaign(BaseModel):
    """Main campaign model"""
    CAMPAIGN_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('running', 'Running'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    CHANNEL_CHOICES = [
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
        ('sms', 'SMS'),
        ('phone', 'Phone Call'),
        ('push', 'Push Notification'),
    ]
    
    name = models.CharField(max_length=200)
    campaign_type = models.ForeignKey(CampaignType, on_delete=models.CASCADE, related_name='campaigns')
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=CAMPAIGN_STATUS_CHOICES, default='draft')
    
    # Campaign Settings
    channels = models.JSONField(default=list, help_text="List of communication channels")
    target_audience = models.CharField(max_length=50, choices=[
        ('all_customers', 'All Customers'),
        ('policy_holders', 'Policy Holders'),
        ('renewal_due', 'Renewal Due'),
        ('custom', 'Custom Segment'),
    ], default='all_customers')
    
    # Scheduling
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.JSONField(default=dict, blank=True)
    
    # Content
    subject_line = models.CharField(max_length=200, blank=True)
    email_template = models.TextField(blank=True)
    whatsapp_template = models.TextField(blank=True)
    sms_template = models.TextField(blank=True)
    
    # Personalization
    use_personalization = models.BooleanField(default=True)
    personalization_fields = models.JSONField(default=list, blank=True)
    
    # Tracking
    total_recipients = models.PositiveIntegerField(default=0)
    total_sent = models.PositiveIntegerField(default=0)
    total_delivered = models.PositiveIntegerField(default=0)
    total_opened = models.PositiveIntegerField(default=0)
    total_clicked = models.PositiveIntegerField(default=0)
    total_responses = models.PositiveIntegerField(default=0)
    
    # System Fields
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_campaigns')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_campaigns')
    
    class Meta:
        db_table = 'campaigns'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'start_date']),
            models.Index(fields=['campaign_type', 'status']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.status})"
    
    @property
    def delivery_rate(self):
        """Calculate delivery rate percentage"""
        if self.total_sent == 0:
            return 0
        return round((self.total_delivered / self.total_sent) * 100, 2)
    
    @property
    def open_rate(self):
        """Calculate open rate percentage"""
        if self.total_delivered == 0:
            return 0
        return round((self.total_opened / self.total_delivered) * 100, 2)
    
    @property
    def click_rate(self):
        """Calculate click rate percentage"""
        if self.total_opened == 0:
            return 0
        return round((self.total_clicked / self.total_opened) * 100, 2)
    
    @property
    def response_rate(self):
        """Calculate response rate percentage"""
        if self.total_delivered == 0:
            return 0
        return round((self.total_responses / self.total_delivered) * 100, 2)

class CampaignSegment(BaseModel):
    """Customer segments for targeted campaigns"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    criteria = models.JSONField(default=dict, help_text="Segmentation criteria in JSON format")
    
    # Criteria examples:
    # {
    #   "policy_status": ["active", "expired"],
    #   "days_to_expiry": {"min": 0, "max": 30},
    #   "premium_range": {"min": 10000, "max": 50000},
    #   "policy_types": ["LIFE", "HEALTH"],
    #   "customer_age": {"min": 25, "max": 65}
    # }
    
    customer_count = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'campaign_segments'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.customer_count} customers)"

class CampaignRecipient(BaseModel):
    """Individual recipients of a campaign"""
    DELIVERY_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
        ('opted_out', 'Opted Out'),
    ]
    
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='recipients')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    policy = models.ForeignKey(Policy, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Delivery tracking per channel
    email_status = models.CharField(max_length=20, choices=DELIVERY_STATUS_CHOICES, default='pending')
    whatsapp_status = models.CharField(max_length=20, choices=DELIVERY_STATUS_CHOICES, default='pending')
    sms_status = models.CharField(max_length=20, choices=DELIVERY_STATUS_CHOICES, default='pending')
    
    # Delivery timestamps
    email_sent_at = models.DateTimeField(null=True, blank=True)
    whatsapp_sent_at = models.DateTimeField(null=True, blank=True)
    sms_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Engagement tracking
    email_opened_at = models.DateTimeField(null=True, blank=True)
    email_clicked_at = models.DateTimeField(null=True, blank=True)
    whatsapp_read_at = models.DateTimeField(null=True, blank=True)
    response_received_at = models.DateTimeField(null=True, blank=True)
    
    # Personalized content
    personalized_content = models.JSONField(default=dict, blank=True)
    
    # Response tracking
    has_responded = models.BooleanField(default=False)
    response_type = models.CharField(max_length=20, choices=[
        ('interested', 'Interested'),
        ('not_interested', 'Not Interested'),
        ('callback_requested', 'Callback Requested'),
        ('complaint', 'Complaint'),
        ('unsubscribe', 'Unsubscribe'),
    ], blank=True)
    response_notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'campaign_recipients'
        unique_together = ['campaign', 'customer']
        indexes = [
            models.Index(fields=['campaign', 'email_status']),
            models.Index(fields=['campaign', 'has_responded']),
        ]
    
    def __str__(self):
        return f"{self.campaign.name} - {self.customer.full_name}"

class CampaignTemplate(BaseModel):
    """Reusable campaign templates"""
    TEMPLATE_TYPE_CHOICES = [
        ('email', 'Email Template'),
        ('whatsapp', 'WhatsApp Template'),
        ('sms', 'SMS Template'),
    ]
    
    name = models.CharField(max_length=200)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPE_CHOICES)
    subject = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    
    # Template variables
    variables = models.JSONField(default=list, help_text="List of template variables")
    # Example: ["customer_name", "policy_number", "expiry_date", "premium_amount"]
    
    # Usage tracking
    usage_count = models.PositiveIntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'campaign_templates'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.template_type})"

class CampaignSchedule(BaseModel):
    """Scheduled campaign executions"""
    SCHEDULE_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='schedules')
    scheduled_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=SCHEDULE_STATUS_CHOICES, default='pending')
    
    # Execution details
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    recipients_processed = models.PositiveIntegerField(default=0)
    
    # Error handling
    error_message = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)
    
    class Meta:
        db_table = 'campaign_schedules'
        ordering = ['-scheduled_at']
    
    def __str__(self):
        return f"{self.campaign.name} - {self.scheduled_at}"

class CampaignAnalytics(BaseModel):
    """Detailed campaign analytics"""
    campaign = models.OneToOneField(Campaign, on_delete=models.CASCADE, related_name='analytics')
    
    # Channel-wise statistics
    email_sent = models.PositiveIntegerField(default=0)
    email_delivered = models.PositiveIntegerField(default=0)
    email_opened = models.PositiveIntegerField(default=0)
    email_clicked = models.PositiveIntegerField(default=0)
    email_bounced = models.PositiveIntegerField(default=0)
    
    whatsapp_sent = models.PositiveIntegerField(default=0)
    whatsapp_delivered = models.PositiveIntegerField(default=0)
    whatsapp_read = models.PositiveIntegerField(default=0)
    whatsapp_replied = models.PositiveIntegerField(default=0)
    
    sms_sent = models.PositiveIntegerField(default=0)
    sms_delivered = models.PositiveIntegerField(default=0)
    sms_replied = models.PositiveIntegerField(default=0)
    
    # Response tracking
    total_responses = models.PositiveIntegerField(default=0)
    interested_responses = models.PositiveIntegerField(default=0)
    not_interested_responses = models.PositiveIntegerField(default=0)
    callback_requests = models.PositiveIntegerField(default=0)
    complaints = models.PositiveIntegerField(default=0)
    unsubscribes = models.PositiveIntegerField(default=0)
    
    # Cost tracking
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cost_per_recipient = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    
    # ROI metrics
    conversions = models.PositiveIntegerField(default=0)
    revenue_generated = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    class Meta:
        db_table = 'campaign_analytics'
    
    def __str__(self):
        return f"Analytics - {self.campaign.name}"

class CampaignFeedback(BaseModel):
    """Customer feedback on campaigns"""
    FEEDBACK_TYPE_CHOICES = [
        ('positive', 'Positive'),
        ('negative', 'Negative'),
        ('neutral', 'Neutral'),
        ('complaint', 'Complaint'),
        ('suggestion', 'Suggestion'),
    ]
    
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='feedback')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPE_CHOICES)
    rating = models.PositiveIntegerField(null=True, blank=True, help_text="Rating from 1-5")
    feedback_text = models.TextField()
    
    # Response details
    channel_received = models.CharField(max_length=20, choices=Campaign.CHANNEL_CHOICES)
    received_at = models.DateTimeField(auto_now_add=True)
    
    # Follow-up
    is_resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'campaign_feedback'
        ordering = ['-received_at']
    
    def __str__(self):
        return f"Feedback - {self.campaign.name} from {self.customer.full_name}"

class CampaignAutomation(BaseModel):
    """Automated campaign triggers"""
    TRIGGER_TYPE_CHOICES = [
        ('policy_expiry', 'Policy Expiry'),
        ('payment_due', 'Payment Due'),
        ('new_customer', 'New Customer'),
        ('claim_status', 'Claim Status Change'),
        ('birthday', 'Customer Birthday'),
        ('anniversary', 'Policy Anniversary'),
    ]
    
    name = models.CharField(max_length=200)
    trigger_type = models.CharField(max_length=30, choices=TRIGGER_TYPE_CHOICES)
    campaign_template = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='automations')
    
    # Trigger conditions
    trigger_conditions = models.JSONField(default=dict)
    # Example for policy_expiry: {"days_before_expiry": 30}
    # Example for payment_due: {"days_after_due": 7}
    
    # Timing
    delay_days = models.PositiveIntegerField(default=0)
    delay_hours = models.PositiveIntegerField(default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    total_triggered = models.PositiveIntegerField(default=0)
    last_triggered = models.DateTimeField(null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'campaign_automations'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.trigger_type})" 