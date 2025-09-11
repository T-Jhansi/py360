"""
Email Operations Models
"""
from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import BaseModel
from django.utils import timezone
import uuid

User = get_user_model()


class EmailMessage(BaseModel):
    """Store sent emails and their metadata"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('queued', 'Queued'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
        ('bounced', 'Bounced'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    # Unique identifier for tracking
    message_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    
    # Email details
    to_email = models.EmailField(help_text="Recipient email address")
    cc_emails = models.JSONField(default=list, blank=True, help_text="CC email addresses")
    bcc_emails = models.JSONField(default=list, blank=True, help_text="BCC email addresses")
    from_email = models.EmailField(help_text="Sender email address")
    from_name = models.CharField(max_length=200, blank=True, help_text="Sender name")
    reply_to = models.EmailField(blank=True, help_text="Reply-to email address")
    
    # Content
    subject = models.CharField(max_length=500, help_text="Email subject")
    html_content = models.TextField(help_text="HTML email content")
    text_content = models.TextField(blank=True, help_text="Plain text content")
    
    # Template reference
    template = models.ForeignKey(
        'email_templates.EmailTemplate', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='sent_emails',
        help_text="Template used for this email"
    )
    template_context = models.JSONField(default=dict, blank=True, help_text="Context used for template rendering")
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    
    # Provider information
    provider_used = models.CharField(max_length=100, blank=True, help_text="Email provider used")
    provider_message_id = models.CharField(max_length=500, blank=True, help_text="Provider's message ID")
    
    # Timing
    scheduled_at = models.DateTimeField(null=True, blank=True, help_text="When to send the email")
    sent_at = models.DateTimeField(null=True, blank=True, help_text="When email was sent")
    delivered_at = models.DateTimeField(null=True, blank=True, help_text="When email was delivered")
    opened_at = models.DateTimeField(null=True, blank=True, help_text="When email was first opened")
    clicked_at = models.DateTimeField(null=True, blank=True, help_text="When email was first clicked")
    
    # Error handling
    error_message = models.TextField(blank=True, help_text="Error message if failed")
    retry_count = models.PositiveIntegerField(default=0, help_text="Number of retry attempts")
    max_retries = models.PositiveIntegerField(default=3, help_text="Maximum retry attempts")
    
    # Tracking
    open_count = models.PositiveIntegerField(default=0, help_text="Number of times opened")
    click_count = models.PositiveIntegerField(default=0, help_text="Number of times clicked")
    bounce_reason = models.TextField(blank=True, help_text="Bounce reason if bounced")
    
    # Metadata
    campaign_id = models.CharField(max_length=100, blank=True, help_text="Campaign identifier")
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    
    class Meta:
        db_table = 'email_messages'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['to_email', 'status']),
            models.Index(fields=['scheduled_at', 'status']),
            models.Index(fields=['template', 'status']),
            models.Index(fields=['campaign_id', 'status']),
            models.Index(fields=['message_id']),
        ]
    
    def __str__(self):
        return f"{self.to_email} - {self.subject} ({self.get_status_display()})"
    
    def mark_as_sent(self, provider_name, provider_message_id):
        """Mark email as sent"""
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.provider_used = provider_name
        self.provider_message_id = provider_message_id
        self.save(update_fields=['status', 'sent_at', 'provider_used', 'provider_message_id'])
    
    def mark_as_delivered(self):
        """Mark email as delivered"""
        self.status = 'delivered'
        self.delivered_at = timezone.now()
        self.save(update_fields=['status', 'delivered_at'])
    
    def mark_as_opened(self):
        """Mark email as opened"""
        if self.status not in ['opened', 'clicked']:
            self.status = 'opened'
            self.opened_at = timezone.now()
        self.open_count += 1
        self.save(update_fields=['status', 'opened_at', 'open_count'])
    
    def mark_as_clicked(self):
        """Mark email as clicked"""
        self.status = 'clicked'
        if not self.clicked_at:
            self.clicked_at = timezone.now()
        self.click_count += 1
        self.save(update_fields=['status', 'clicked_at', 'click_count'])
    
    def mark_as_bounced(self, reason):
        """Mark email as bounced"""
        self.status = 'bounced'
        self.bounce_reason = reason
        self.save(update_fields=['status', 'bounce_reason'])
    
    def mark_as_failed(self, error_message):
        """Mark email as failed"""
        self.status = 'failed'
        self.error_message = error_message
        self.retry_count += 1
        self.save(update_fields=['status', 'error_message', 'retry_count'])
    
    def can_retry(self):
        """Check if email can be retried"""
        return self.retry_count < self.max_retries and self.status in ['failed', 'pending']


class EmailQueue(BaseModel):
    """Email queue for managing email sending"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Queue information
    name = models.CharField(max_length=200, help_text="Queue name")
    description = models.TextField(blank=True, help_text="Queue description")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Processing settings
    batch_size = models.PositiveIntegerField(default=100, help_text="Emails to process per batch")
    delay_between_batches = models.PositiveIntegerField(default=60, help_text="Delay between batches in seconds")
    max_retries = models.PositiveIntegerField(default=3, help_text="Maximum retry attempts")
    
    # Statistics
    total_emails = models.PositiveIntegerField(default=0, help_text="Total emails in queue")
    processed_emails = models.PositiveIntegerField(default=0, help_text="Emails processed")
    failed_emails = models.PositiveIntegerField(default=0, help_text="Emails failed")
    success_rate = models.FloatField(default=0.0, help_text="Success rate percentage")
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True, help_text="When processing started")
    completed_at = models.DateTimeField(null=True, blank=True, help_text="When processing completed")
    estimated_completion = models.DateTimeField(null=True, blank=True, help_text="Estimated completion time")
    
    # Error handling
    error_message = models.TextField(blank=True, help_text="Error message if failed")
    
    class Meta:
        db_table = 'email_queues'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['started_at', 'status']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    def start_processing(self):
        """Start processing the queue"""
        self.status = 'processing'
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])
    
    def complete_processing(self):
        """Mark queue as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.success_rate = (self.processed_emails / self.total_emails * 100) if self.total_emails > 0 else 0
        self.save(update_fields=['status', 'completed_at', 'success_rate'])
    
    def fail_processing(self, error_message):
        """Mark queue as failed"""
        self.status = 'failed'
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message'])


class EmailTracking(BaseModel):
    """Track email interactions (opens, clicks, etc.)"""
    
    EVENT_TYPES = [
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
        ('bounced', 'Bounced'),
        ('unsubscribed', 'Unsubscribed'),
        ('complained', 'Complained'),
    ]
    
    # Email reference
    email = models.ForeignKey(EmailMessage, on_delete=models.CASCADE, related_name='tracking_events')
    
    # Event details
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    event_data = models.JSONField(default=dict, blank=True, help_text="Additional event data")
    
    # Tracking details
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="IP address of the event")
    user_agent = models.TextField(blank=True, help_text="User agent string")
    referrer = models.URLField(blank=True, help_text="Referrer URL")
    
    # Click tracking specific
    clicked_url = models.URLField(blank=True, help_text="URL that was clicked")
    link_text = models.CharField(max_length=500, blank=True, help_text="Text of the clicked link")
    
    # Timing
    event_timestamp = models.DateTimeField(default=timezone.now, help_text="When the event occurred")
    
    class Meta:
        db_table = 'email_tracking'
        ordering = ['-event_timestamp']
        indexes = [
            models.Index(fields=['email', 'event_type']),
            models.Index(fields=['event_type', 'event_timestamp']),
            models.Index(fields=['ip_address', 'event_timestamp']),
        ]
    
    def __str__(self):
        return f"{self.email.to_email} - {self.get_event_type_display()} at {self.event_timestamp}"


class EmailDeliveryReport(BaseModel):
    """Daily delivery reports for email performance"""
    
    # Report period
    report_date = models.DateField(help_text="Date this report covers")
    
    # Provider information
    provider_name = models.CharField(max_length=100, help_text="Email provider name")
    
    # Statistics
    total_sent = models.PositiveIntegerField(default=0, help_text="Total emails sent")
    total_delivered = models.PositiveIntegerField(default=0, help_text="Total emails delivered")
    total_opened = models.PositiveIntegerField(default=0, help_text="Total emails opened")
    total_clicked = models.PositiveIntegerField(default=0, help_text="Total emails clicked")
    total_bounced = models.PositiveIntegerField(default=0, help_text="Total emails bounced")
    total_failed = models.PositiveIntegerField(default=0, help_text="Total emails failed")
    
    # Rates
    delivery_rate = models.FloatField(default=0.0, help_text="Delivery rate percentage")
    open_rate = models.FloatField(default=0.0, help_text="Open rate percentage")
    click_rate = models.FloatField(default=0.0, help_text="Click rate percentage")
    bounce_rate = models.FloatField(default=0.0, help_text="Bounce rate percentage")
    
    # Performance metrics
    avg_response_time = models.FloatField(default=0.0, help_text="Average response time in seconds")
    success_rate = models.FloatField(default=0.0, help_text="Overall success rate percentage")
    
    # Additional data
    report_data = models.JSONField(default=dict, blank=True, help_text="Additional report data")
    
    class Meta:
        db_table = 'email_delivery_reports'
        ordering = ['-report_date']
        unique_together = ['report_date', 'provider_name']
        indexes = [
            models.Index(fields=['report_date', 'provider_name']),
            models.Index(fields=['provider_name', 'report_date']),
        ]
    
    def __str__(self):
        return f"{self.provider_name} - {self.report_date} (Success: {self.success_rate:.1f}%)"
    
    def calculate_rates(self):
        """Calculate all rates based on statistics"""
        if self.total_sent > 0:
            self.delivery_rate = (self.total_delivered / self.total_sent) * 100
            self.open_rate = (self.total_opened / self.total_sent) * 100
            self.click_rate = (self.total_clicked / self.total_sent) * 100
            self.bounce_rate = (self.total_bounced / self.total_sent) * 100
            self.success_rate = ((self.total_delivered + self.total_opened + self.total_clicked) / self.total_sent) * 100


class EmailAnalytics(BaseModel):
    """Email performance analytics and insights"""
    
    # Analytics period
    period_start = models.DateTimeField(help_text="Start of analytics period")
    period_end = models.DateTimeField(help_text="End of analytics period")
    
    # Template analytics
    template = models.ForeignKey(
        'email_templates.EmailTemplate', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='analytics'
    )
    
    # Campaign analytics
    campaign_id = models.CharField(max_length=100, blank=True, help_text="Campaign identifier")
    
    # Performance metrics
    total_sent = models.PositiveIntegerField(default=0)
    total_delivered = models.PositiveIntegerField(default=0)
    total_opened = models.PositiveIntegerField(default=0)
    total_clicked = models.PositiveIntegerField(default=0)
    total_bounced = models.PositiveIntegerField(default=0)
    total_unsubscribed = models.PositiveIntegerField(default=0)
    
    # Rates
    delivery_rate = models.FloatField(default=0.0)
    open_rate = models.FloatField(default=0.0)
    click_rate = models.FloatField(default=0.0)
    bounce_rate = models.FloatField(default=0.0)
    unsubscribe_rate = models.FloatField(default=0.0)
    
    # Engagement metrics
    unique_opens = models.PositiveIntegerField(default=0, help_text="Unique email opens")
    unique_clicks = models.PositiveIntegerField(default=0, help_text="Unique email clicks")
    click_to_open_rate = models.FloatField(default=0.0, help_text="Click-to-open rate")
    
    # Timing metrics
    avg_time_to_open = models.FloatField(default=0.0, help_text="Average time to open in minutes")
    avg_time_to_click = models.FloatField(default=0.0, help_text="Average time to click in minutes")
    
    # Additional insights
    insights = models.JSONField(default=dict, blank=True, help_text="Additional analytics insights")
    
    class Meta:
        db_table = 'email_analytics'
        ordering = ['-period_end']
        indexes = [
            models.Index(fields=['period_start', 'period_end']),
            models.Index(fields=['template', 'period_end']),
            models.Index(fields=['campaign_id', 'period_end']),
        ]
    
    def __str__(self):
        return f"Analytics {self.period_start.date()} - {self.period_end.date()} (Open: {self.open_rate:.1f}%)"
    
    def calculate_metrics(self):
        """Calculate all metrics based on data"""
        if self.total_sent > 0:
            self.delivery_rate = (self.total_delivered / self.total_sent) * 100
            self.open_rate = (self.total_opened / self.total_sent) * 100
            self.click_rate = (self.total_clicked / self.total_sent) * 100
            self.bounce_rate = (self.total_bounced / self.total_sent) * 100
            self.unsubscribe_rate = (self.total_unsubscribed / self.total_sent) * 100
        
        if self.total_opened > 0:
            self.click_to_open_rate = (self.total_clicked / self.total_opened) * 100
