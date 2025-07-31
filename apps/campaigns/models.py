from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import BaseModel, TimestampedModel
from apps.customers.models import Customer
from apps.policies.models import Policy
from apps.templates.models import Template
from apps.files_upload.models import FileUpload
from apps.TargetAudience.models import TargetAudience
from decimal import Decimal
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
    template = models.ForeignKey(Template, on_delete=models.SET_NULL, null=True, blank=True, related_name='campaigns')
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=CAMPAIGN_STATUS_CHOICES, default='draft')
    upload = models.ForeignKey(FileUpload,on_delete=models.SET_NULL,null=True,blank=True,related_name='campaigns')
    # Campaign Settings
    channels = models.JSONField(default=list, help_text="List of communication channels")
    target_audience = models.ForeignKey(TargetAudience,on_delete=models.SET_NULL, null=True, blank=True, related_name='campaigns'
    )

    # Scheduling
    schedule_type = models.CharField(max_length=20, choices=[
        ('immediate', 'Immediate'),
        ('schedule later', 'Scheduled Later'),
    ], default='immediate')
    scheduled_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)

    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.JSONField(default=dict, blank=True)
    
    # Content
    subject_line = models.CharField(max_length=200, blank=True)
    
    # Personalization
    use_personalization = models.BooleanField(default=True)
    personalization_fields = models.JSONField(default=list, blank=True)
    
    # Tracking
    target_count = models.PositiveIntegerField(default=0)
    sent_count = models.PositiveIntegerField(default=0)
    delivered_count = models.PositiveIntegerField(default=0)
    opened_count = models.PositiveIntegerField(default=0)
    clicked_count = models.PositiveIntegerField(default=0)
    total_responses = models.PositiveIntegerField(default=0)
    
    # System Fields
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_campaigns')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_campaigns')
    
    class Meta:
        db_table = 'campaigns'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'started_at']),
            models.Index(fields=['campaign_type', 'status']),
        ]

    def __str__(self):
        return f"{self.name} ({self.status})"

    def update_campaign_statistics(self):
        """Update campaign statistics based on recipient data"""
        recipients = self.recipients.all()

        # Count sent emails (status = 'sent')
        self.sent_count = recipients.filter(email_status='sent').count()

        # Count delivered emails (emails that have been opened/clicked - meaning they were delivered)
        self.delivered_count = recipients.filter(
            email_delivered_at__isnull=False
        ).count()

        # Count opened emails (opened, clicked, replied, forwarded)
        self.opened_count = recipients.filter(
            email_engagement__in=['opened', 'clicked', 'replied', 'forwarded']
        ).count()

        # Count clicked emails (clicked, replied, forwarded)
        self.clicked_count = recipients.filter(
            email_engagement__in=['clicked', 'replied', 'forwarded']
        ).count()

        # Count total responses (replied, forwarded, etc.)
        self.total_responses = recipients.filter(
            email_engagement__in=['replied', 'forwarded']
        ).count()

        self.save(update_fields=[
            'sent_count', 'delivered_count', 'opened_count',
            'clicked_count', 'total_responses'
        ])

    def get_campaign_metrics(self):
        """Get comprehensive campaign metrics"""
        recipients = self.recipients.all()
        total_recipients = recipients.count()

        if total_recipients == 0:
            return {
                'total_recipients': 0,
                'sent_rate': 0,
                'delivery_rate': 0,
                'open_rate': 0,
                'click_rate': 0,
                'response_rate': 0
            }

        return {
            'total_recipients': total_recipients,
            'sent_count': self.sent_count,
            'delivered_count': self.delivered_count,
            'opened_count': self.opened_count,
            'clicked_count': self.clicked_count,
            'total_responses': self.total_responses,
            'sent_rate': round((self.sent_count / total_recipients) * 100, 2),
            'delivery_rate': round((self.delivered_count / self.sent_count) * 100, 2) if self.sent_count > 0 else 0,
            'open_rate': round((self.opened_count / self.delivered_count) * 100, 2) if self.delivered_count > 0 else 0,
            'click_rate': round((self.clicked_count / self.opened_count) * 100, 2) if self.opened_count > 0 else 0,
            'response_rate': round((self.total_responses / total_recipients) * 100, 2)
        }
    
    @property
    def delivery_rate(self):
        """Calculate delivery rate percentage"""
        if self.sent_count == 0:
            return 0
        return round((self.delivered_count / self.sent_count) * 100, 2)
    
    @property
    def open_rate(self):
        """Calculate open rate percentage"""
        if self.delivered_count == 0:
            return 0
        return round((self.opened_count / self.delivered_count) * 100, 2)
    
    @property
    def click_rate(self):
        """Calculate click rate percentage"""
        if self.opened_count == 0:
            return 0
        return round((self.clicked_count / self.opened_count) * 100, 2)
    
    @property
    def response_rate(self):
        """Calculate response rate percentage"""
        if self.delivered_count == 0:
            return 0
        return round((self.total_responses / self.delivered_count) * 100, 2)

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
    """Individual recipients of a campaign with enhanced tracking"""
    DELIVERY_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('queued', 'Queued'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
        ('rejected', 'Rejected'),
        ('opted_out', 'Opted Out'),
        ('blocked', 'Blocked'),
    ]

    ENGAGEMENT_STATUS_CHOICES = [
        ('not_opened', 'Not Opened'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
        ('replied', 'Replied'),
        ('forwarded', 'Forwarded'),
        ('unsubscribed', 'Unsubscribed'),
    ]

    # Core relationships
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='recipients')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='campaign_recipients')
    policy = models.ForeignKey(Policy, on_delete=models.SET_NULL, null=True, blank=True, related_name='campaign_recipients')

    # Channel-specific delivery tracking
    email_status = models.CharField(max_length=20, choices=DELIVERY_STATUS_CHOICES, default='pending')
    whatsapp_status = models.CharField(max_length=20, choices=DELIVERY_STATUS_CHOICES, default='pending')
    sms_status = models.CharField(max_length=20, choices=DELIVERY_STATUS_CHOICES, default='pending')

    # Channel-specific engagement tracking
    email_engagement = models.CharField(max_length=20, choices=ENGAGEMENT_STATUS_CHOICES, default='not_opened')
    whatsapp_engagement = models.CharField(max_length=20, choices=ENGAGEMENT_STATUS_CHOICES, default='not_opened')
    sms_engagement = models.CharField(max_length=20, choices=ENGAGEMENT_STATUS_CHOICES, default='not_opened')

    # Unique tracking ID for secure tracking
    tracking_id = models.CharField(max_length=64, unique=True, blank=True)

    # Delivery timestamps
    email_sent_at = models.DateTimeField(null=True, blank=True)
    email_delivered_at = models.DateTimeField(null=True, blank=True)
    whatsapp_sent_at = models.DateTimeField(null=True, blank=True)
    whatsapp_delivered_at = models.DateTimeField(null=True, blank=True)
    sms_sent_at = models.DateTimeField(null=True, blank=True)
    sms_delivered_at = models.DateTimeField(null=True, blank=True)

    # Engagement timestamps
    email_opened_at = models.DateTimeField(null=True, blank=True)
    email_clicked_at = models.DateTimeField(null=True, blank=True)
    email_replied_at = models.DateTimeField(null=True, blank=True)
    whatsapp_read_at = models.DateTimeField(null=True, blank=True)
    whatsapp_replied_at = models.DateTimeField(null=True, blank=True)
    sms_replied_at = models.DateTimeField(null=True, blank=True)

    # Error tracking
    email_error_message = models.TextField(blank=True)
    whatsapp_error_message = models.TextField(blank=True)
    sms_error_message = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)

    # Personalized content for each channel
    email_content = models.JSONField(default=dict, blank=True, help_text="Personalized email content")
    whatsapp_content = models.JSONField(default=dict, blank=True, help_text="Personalized WhatsApp content")
    sms_content = models.JSONField(default=dict, blank=True, help_text="Personalized SMS content")

    # Response tracking
    has_responded = models.BooleanField(default=False)
    response_channel = models.CharField(max_length=20, choices=Campaign.CHANNEL_CHOICES, blank=True)
    response_type = models.CharField(max_length=30, choices=[
        ('interested', 'Interested'),
        ('not_interested', 'Not Interested'),
        ('callback_requested', 'Callback Requested'),
        ('more_info_requested', 'More Info Requested'),
        ('complaint', 'Complaint'),
        ('unsubscribe', 'Unsubscribe'),
        ('policy_renewed', 'Policy Renewed'),
        ('payment_made', 'Payment Made'),
        ('document_requested', 'Document Requested'),
    ], blank=True)
    response_notes = models.TextField(blank=True)
    response_received_at = models.DateTimeField(null=True, blank=True)

    # Campaign effectiveness tracking
    conversion_achieved = models.BooleanField(default=False, help_text="Did this recipient convert (renew/purchase)?")
    conversion_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Value of conversion")
    conversion_date = models.DateTimeField(null=True, blank=True)

    # Additional metadata
    recipient_metadata = models.JSONField(default=dict, blank=True, help_text="Additional recipient-specific data")

    class Meta:
        db_table = 'campaign_recipients'
        unique_together = ['campaign', 'customer']
        indexes = [
            models.Index(fields=['campaign', 'email_status']),
            models.Index(fields=['campaign', 'whatsapp_status']),
            models.Index(fields=['campaign', 'sms_status']),
            models.Index(fields=['campaign', 'has_responded']),
            models.Index(fields=['campaign', 'conversion_achieved']),
            models.Index(fields=['email_status', 'email_sent_at']),
            models.Index(fields=['customer', 'campaign']),
            models.Index(fields=['response_type', 'response_received_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.campaign.name} - {self.customer.full_name}"

    def save(self, *args, **kwargs):
        """Generate tracking ID if not exists"""
        if not self.tracking_id:
            import uuid
            import hashlib
            # Create a unique tracking ID using campaign, customer, and timestamp
            unique_string = f"{self.campaign_id}-{self.customer_id}-{uuid.uuid4()}"
            self.tracking_id = hashlib.sha256(unique_string.encode()).hexdigest()[:32]
        super().save(*args, **kwargs)

    @property
    def primary_status(self):
        """Get the primary delivery status based on campaign channels"""
        if 'email' in self.campaign.channels:
            return self.email_status
        elif 'whatsapp' in self.campaign.channels:
            return self.whatsapp_status
        elif 'sms' in self.campaign.channels:
            return self.sms_status
        return 'pending'

    @property
    def is_delivered(self):
        """Check if message was delivered on any channel"""
        return (self.email_status == 'delivered' or
                self.whatsapp_status == 'delivered' or
                self.sms_status == 'delivered')

    @property
    def is_engaged(self):
        """Check if recipient engaged with any channel"""
        return (self.email_engagement in ['opened', 'clicked', 'replied'] or
                self.whatsapp_engagement in ['opened', 'clicked', 'replied'] or
                self.sms_engagement in ['opened', 'clicked', 'replied'])

    def mark_sent(self, channel, timestamp=None):
        """Mark message as sent for specific channel"""
        from django.utils import timezone
        if timestamp is None:
            timestamp = timezone.now()

        if channel == 'email':
            self.email_status = 'sent'
            self.email_sent_at = timestamp
        elif channel == 'whatsapp':
            self.whatsapp_status = 'sent'
            self.whatsapp_sent_at = timestamp
        elif channel == 'sms':
            self.sms_status = 'sent'
            self.sms_sent_at = timestamp
        self.save()

    def mark_delivered(self, channel, timestamp=None):
        """Mark message as delivered for specific channel"""
        from django.utils import timezone
        if timestamp is None:
            timestamp = timezone.now()

        if channel == 'email':
            self.email_status = 'delivered'
            self.email_delivered_at = timestamp
        elif channel == 'whatsapp':
            self.whatsapp_status = 'delivered'
            self.whatsapp_delivered_at = timestamp
        elif channel == 'sms':
            self.sms_status = 'delivered'
            self.sms_delivered_at = timestamp
        self.save()

    def mark_opened(self, channel, timestamp=None):
        """Mark message as opened for specific channel"""
        from django.utils import timezone
        if timestamp is None:
            timestamp = timezone.now()

        if channel == 'email':
            self.email_engagement = 'opened'
            self.email_opened_at = timestamp
        elif channel == 'whatsapp':
            self.whatsapp_engagement = 'opened'
            self.whatsapp_read_at = timestamp
        self.save()

    def mark_failed(self, channel, error_message="", timestamp=None):
        """Mark message as failed for specific channel"""
        from django.utils import timezone
        if timestamp is None:
            timestamp = timezone.now()

        if channel == 'email':
            self.email_status = 'failed'
            self.email_error_message = error_message
        elif channel == 'whatsapp':
            self.whatsapp_status = 'failed'
            self.whatsapp_error_message = error_message
        elif channel == 'sms':
            self.sms_status = 'failed'
            self.sms_error_message = error_message

        self.retry_count += 1
        self.save()

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
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    cost_per_recipient = models.DecimalField(max_digits=8, decimal_places=4, default=Decimal('0.0000'))

    # ROI metrics
    conversions = models.PositiveIntegerField(default=0)
    revenue_generated = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
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