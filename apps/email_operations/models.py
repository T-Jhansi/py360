from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date
import uuid

User = get_user_model()


class EmailMessage(models.Model):
    """Email messages for sending, tracking, and analytics"""
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
        ('complained', 'Complained'),
        ('unsubscribed', 'Unsubscribed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message_id = models.CharField(max_length=255, unique=True, help_text="Unique message identifier")
    
    # Recipients
    to_email = models.EmailField()
    cc_emails = models.JSONField(default=list, blank=True, help_text="CC email addresses")
    bcc_emails = models.JSONField(default=list, blank=True, help_text="BCC email addresses")
    
    # Sender information
    from_email = models.EmailField()
    from_name = models.CharField(max_length=100, blank=True, null=True)
    reply_to = models.EmailField(blank=True, null=True)
    
    # Email content
    subject = models.CharField(max_length=500)
    html_content = models.TextField(blank=True, null=True)
    text_content = models.TextField(blank=True, null=True)
    
    # Template information
    template_id = models.UUIDField(blank=True, null=True, help_text="ID of the email template used")
    template_name = models.CharField(max_length=200, blank=True, null=True)
    template_variables = models.JSONField(default=dict, blank=True, help_text="Variables used in template")
    
    # Email settings
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Scheduling
    scheduled_at = models.DateTimeField(blank=True, null=True, help_text="When to send the email")
    sent_at = models.DateTimeField(blank=True, null=True, help_text="When the email was actually sent")
    
    # Campaign and tracking
    campaign_id = models.CharField(max_length=100, blank=True, null=True, help_text="Campaign identifier")
    tags = models.JSONField(default=list, blank=True, help_text="Tags for categorization")
    
    # Provider information
    provider_name = models.CharField(max_length=100, blank=True, null=True, help_text="Email provider used")
    provider_message_id = models.CharField(max_length=255, blank=True, null=True, help_text="Provider's message ID")
    
    # Error handling
    error_message = models.TextField(blank=True, null=True)
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_email_messages')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_email_messages')
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deleted_email_messages')
    
    class Meta:
        db_table = 'email_messages'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['to_email', 'status']),
            models.Index(fields=['campaign_id', 'status']),
            models.Index(fields=['scheduled_at', 'status']),
            models.Index(fields=['created_at', 'status']),
        ]
        verbose_name = 'Email Message'
        verbose_name_plural = 'Email Messages'
    
    def __str__(self):
        return f"{self.subject} -> {self.to_email}"
    
    def soft_delete(self):
        """Soft delete the email message"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])


class EmailQueue(models.Model):
    """Queue for managing email sending"""
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email_message = models.OneToOneField(EmailMessage, on_delete=models.CASCADE, related_name='queue_entry')
    
    # Queue settings
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    
    # Processing
    scheduled_for = models.DateTimeField(default=timezone.now, help_text="When to process this email")
    processed_at = models.DateTimeField(blank=True, null=True)
    attempts = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=3)
    
    # Error handling
    error_message = models.TextField(blank=True, null=True)
    last_error = models.TextField(blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'email_queue'
        ordering = ['scheduled_for', 'priority']
        indexes = [
            models.Index(fields=['status', 'scheduled_for']),
            models.Index(fields=['priority', 'scheduled_for']),
        ]
        verbose_name = 'Email Queue Entry'
        verbose_name_plural = 'Email Queue Entries'
    
    def __str__(self):
        return f"Queue: {self.email_message.subject} ({self.status})"


class EmailTracking(models.Model):
    """Email tracking and analytics"""
    
    EVENT_CHOICES = [
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
        ('bounced', 'Bounced'),
        ('complained', 'Complained'),
        ('unsubscribed', 'Unsubscribed'),
        ('blocked', 'Blocked'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email_message = models.ForeignKey(EmailMessage, on_delete=models.CASCADE, related_name='tracking_events')
    
    # Event details
    event_type = models.CharField(max_length=20, choices=EVENT_CHOICES)
    event_data = models.JSONField(default=dict, blank=True, help_text="Additional event data")
    
    # Tracking information
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    
    # Link tracking (for clicked events)
    link_url = models.URLField(blank=True, null=True)
    link_text = models.CharField(max_length=500, blank=True, null=True)
    
    # Timestamp
    event_time = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'email_tracking'
        ordering = ['-event_time']
        indexes = [
            models.Index(fields=['email_message', 'event_type']),
            models.Index(fields=['event_type', 'event_time']),
        ]
        verbose_name = 'Email Tracking Event'
        verbose_name_plural = 'Email Tracking Events'
    
    def __str__(self):
        return f"{self.email_message.subject} - {self.get_event_type_display()}"


class EmailDeliveryReport(models.Model):
    """Delivery reports from email providers"""
    
    STATUS_CHOICES = [
        ('delivered', 'Delivered'),
        ('bounced', 'Bounced'),
        ('complained', 'Complained'),
        ('unsubscribed', 'Unsubscribed'),
        ('blocked', 'Blocked'),
        ('deferred', 'Deferred'),
        ('dropped', 'Dropped'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email_message = models.ForeignKey(EmailMessage, on_delete=models.CASCADE, related_name='delivery_reports')
    
    # Provider information
    provider_name = models.CharField(max_length=100)
    provider_message_id = models.CharField(max_length=255)
    
    # Delivery details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    status_message = models.TextField(blank=True, null=True)
    response_time = models.FloatField(blank=True, null=True, help_text="Response time in seconds")
    
    # Additional data
    raw_data = models.JSONField(default=dict, blank=True, help_text="Raw provider response data")
    
    # Timestamp
    reported_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'email_delivery_reports'
        ordering = ['-reported_at']
        indexes = [
            models.Index(fields=['email_message', 'status']),
            models.Index(fields=['provider_name', 'status']),
        ]
        verbose_name = 'Email Delivery Report'
        verbose_name_plural = 'Email Delivery Reports'
    
    def __str__(self):
        return f"{self.email_message.subject} - {self.get_status_display()}"


class EmailAnalytics(models.Model):
    """Email analytics and reporting"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Time period
    date = models.DateField()
    period_type = models.CharField(max_length=20, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ], default='daily')
    
    # Campaign information
    campaign_id = models.CharField(max_length=100, blank=True, null=True)
    template_id = models.UUIDField(blank=True, null=True)
    
    # Metrics
    emails_sent = models.PositiveIntegerField(default=0)
    emails_delivered = models.PositiveIntegerField(default=0)
    emails_opened = models.PositiveIntegerField(default=0)
    emails_clicked = models.PositiveIntegerField(default=0)
    emails_bounced = models.PositiveIntegerField(default=0)
    emails_complained = models.PositiveIntegerField(default=0)
    emails_unsubscribed = models.PositiveIntegerField(default=0)
    
    # Calculated metrics
    delivery_rate = models.FloatField(default=0.0, help_text="Delivery rate percentage")
    open_rate = models.FloatField(default=0.0, help_text="Open rate percentage")
    click_rate = models.FloatField(default=0.0, help_text="Click rate percentage")
    bounce_rate = models.FloatField(default=0.0, help_text="Bounce rate percentage")
    complaint_rate = models.FloatField(default=0.0, help_text="Complaint rate percentage")
    unsubscribe_rate = models.FloatField(default=0.0, help_text="Unsubscribe rate percentage")
    
    # Response times
    avg_response_time = models.FloatField(default=0.0, help_text="Average response time in seconds")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'email_analytics'
        ordering = ['-date']
        unique_together = ['date', 'period_type', 'campaign_id', 'template_id']
        indexes = [
            models.Index(fields=['date', 'period_type']),
            models.Index(fields=['campaign_id', 'date']),
            models.Index(fields=['template_id', 'date']),
        ]
        verbose_name = 'Email Analytics'
        verbose_name_plural = 'Email Analytics'
    
    def __str__(self):
        return f"Analytics - {self.date} ({self.period_type})"
    
    def calculate_rates(self):
        """Calculate all rates based on the metrics"""
        if self.emails_sent > 0:
            self.delivery_rate = (self.emails_delivered / self.emails_sent) * 100
            self.open_rate = (self.emails_opened / self.emails_delivered) * 100 if self.emails_delivered > 0 else 0
            self.click_rate = (self.emails_clicked / self.emails_delivered) * 100 if self.emails_delivered > 0 else 0
            self.bounce_rate = (self.emails_bounced / self.emails_sent) * 100
            self.complaint_rate = (self.emails_complained / self.emails_sent) * 100
            self.unsubscribe_rate = (self.emails_unsubscribed / self.emails_sent) * 100
        else:
            self.delivery_rate = 0
            self.open_rate = 0
            self.click_rate = 0
            self.bounce_rate = 0
            self.complaint_rate = 0
            self.unsubscribe_rate = 0
        
        self.save(update_fields=[
            'delivery_rate', 'open_rate', 'click_rate',
            'bounce_rate', 'complaint_rate', 'unsubscribe_rate'
        ])
