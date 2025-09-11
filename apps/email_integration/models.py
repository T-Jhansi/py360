"""
Email Integration Models
"""
from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import BaseModel
from django.utils import timezone
import uuid

User = get_user_model()


class EmailWebhook(BaseModel):
    """Email provider webhook events"""
    
    PROVIDER_CHOICES = [
        ('sendgrid', 'SendGrid'),
        ('aws_ses', 'AWS SES'),
        ('mailgun', 'Mailgun'),
        ('postmark', 'Postmark'),
        ('mandrill', 'Mandrill'),
        ('smtp', 'SMTP'),
    ]
    
    EVENT_TYPE_CHOICES = [
        ('delivered', 'Delivered'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
        ('bounced', 'Bounced'),
        ('dropped', 'Dropped'),
        ('spam_report', 'Spam Report'),
        ('unsubscribe', 'Unsubscribe'),
        ('processed', 'Processed'),
        ('deferred', 'Deferred'),
        ('blocked', 'Blocked'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processed', 'Processed'),
        ('failed', 'Failed'),
        ('ignored', 'Ignored'),
    ]
    
    # Webhook identification
    webhook_id = models.UUIDField(default=uuid.uuid4, unique=True, help_text="Unique webhook ID")
    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES, help_text="Email provider")
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES, help_text="Webhook event type")
    
    # Webhook data
    webhook_data = models.JSONField(help_text="Raw webhook payload")
    processed_data = models.JSONField(default=dict, help_text="Processed webhook data")
    
    # Email reference
    email_message_id = models.CharField(max_length=500, blank=True, help_text="Related email message ID")
    email_id = models.ForeignKey(
        'email_operations.EmailMessage',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='webhooks',
        help_text="Related email message"
    )
    
    # Processing status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    processed_at = models.DateTimeField(null=True, blank=True, help_text="When webhook was processed")
    processing_attempts = models.PositiveIntegerField(default=0, help_text="Number of processing attempts")
    error_message = models.TextField(blank=True, help_text="Error message if processing failed")
    
    # Timing
    received_at = models.DateTimeField(default=timezone.now, help_text="When webhook was received")
    provider_timestamp = models.DateTimeField(null=True, blank=True, help_text="Provider timestamp")
    
    # Security
    signature = models.CharField(max_length=500, blank=True, help_text="Webhook signature for verification")
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="Source IP address")
    
    class Meta:
        db_table = 'email_webhooks'
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['provider', 'event_type']),
            models.Index(fields=['status', 'received_at']),
            models.Index(fields=['email_message_id']),
            models.Index(fields=['received_at']),
        ]
    
    def __str__(self):
        return f"{self.provider} - {self.event_type} - {self.received_at}"
    
    def mark_processed(self):
        """Mark webhook as processed"""
        self.status = 'processed'
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'processed_at'])
    
    def mark_failed(self, error_message):
        """Mark webhook as failed"""
        self.status = 'failed'
        self.error_message = error_message
        self.processing_attempts += 1
        self.save(update_fields=['status', 'error_message', 'processing_attempts'])


class EmailAutomation(BaseModel):
    """Email automation rules and workflows"""
    
    TRIGGER_TYPE_CHOICES = [
        ('email_received', 'Email Received'),
        ('email_sent', 'Email Sent'),
        ('email_opened', 'Email Opened'),
        ('email_clicked', 'Email Clicked'),
        ('email_bounced', 'Email Bounced'),
        ('time_based', 'Time Based'),
        ('webhook', 'Webhook'),
        ('manual', 'Manual'),
    ]
    
    ACTION_TYPE_CHOICES = [
        ('send_email', 'Send Email'),
        ('reply_email', 'Reply Email'),
        ('forward_email', 'Forward Email'),
        ('move_to_folder', 'Move to Folder'),
        ('add_tag', 'Add Tag'),
        ('remove_tag', 'Remove Tag'),
        ('set_priority', 'Set Priority'),
        ('assign_to_user', 'Assign to User'),
        ('create_task', 'Create Task'),
        ('update_customer', 'Update Customer'),
        ('webhook_call', 'Webhook Call'),
        ('delay', 'Delay'),
    ]
    
    name = models.CharField(max_length=100, help_text="Automation name")
    description = models.TextField(blank=True, help_text="Automation description")
    
    # Trigger configuration
    trigger_type = models.CharField(max_length=50, choices=TRIGGER_TYPE_CHOICES, help_text="Trigger type")
    trigger_conditions = models.JSONField(help_text="Trigger conditions and rules")
    
    # Action configuration
    actions = models.JSONField(help_text="Actions to perform when triggered")
    
    # Status and execution
    is_active = models.BooleanField(default=True, help_text="Automation is active")
    execution_count = models.PositiveIntegerField(default=0, help_text="Number of times executed")
    last_executed_at = models.DateTimeField(null=True, blank=True, help_text="Last execution time")
    success_count = models.PositiveIntegerField(default=0, help_text="Successful executions")
    failure_count = models.PositiveIntegerField(default=0, help_text="Failed executions")
    
    # Timing
    delay_seconds = models.PositiveIntegerField(default=0, help_text="Delay before execution (seconds)")
    max_executions = models.PositiveIntegerField(null=True, blank=True, help_text="Maximum executions (null = unlimited)")
    
    # Advanced settings
    run_once_per_email = models.BooleanField(default=True, help_text="Run only once per email")
    run_once_per_customer = models.BooleanField(default=False, help_text="Run only once per customer")
    priority = models.PositiveIntegerField(default=0, help_text="Execution priority (higher = first)")
    
    class Meta:
        db_table = 'email_automations'
        ordering = ['-priority', 'name']
        indexes = [
            models.Index(fields=['is_active', 'trigger_type']),
            models.Index(fields=['last_executed_at']),
            models.Index(fields=['priority']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_trigger_type_display()})"
    
    def increment_execution_count(self):
        """Increment execution count and update last executed time"""
        self.execution_count += 1
        self.last_executed_at = timezone.now()
        self.save(update_fields=['execution_count', 'last_executed_at'])
    
    def increment_success_count(self):
        """Increment success count"""
        self.success_count += 1
        self.save(update_fields=['success_count'])
    
    def increment_failure_count(self):
        """Increment failure count"""
        self.failure_count += 1
        self.save(update_fields=['failure_count'])


class EmailIntegrationAnalytics(BaseModel):
    """Email integration analytics and performance metrics"""
    
    # Time period
    date = models.DateField(help_text="Analytics date")
    period_type = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('yearly', 'Yearly'),
        ],
        default='daily',
        help_text="Analytics period type"
    )
    
    # Email volume metrics
    total_emails_received = models.PositiveIntegerField(default=0, help_text="Total emails received")
    total_emails_sent = models.PositiveIntegerField(default=0, help_text="Total emails sent")
    total_emails_replied = models.PositiveIntegerField(default=0, help_text="Total emails replied")
    total_emails_forwarded = models.PositiveIntegerField(default=0, help_text="Total emails forwarded")
    
    # Response time metrics
    avg_response_time_minutes = models.FloatField(default=0.0, help_text="Average response time in minutes")
    min_response_time_minutes = models.FloatField(default=0.0, help_text="Minimum response time in minutes")
    max_response_time_minutes = models.FloatField(default=0.0, help_text="Maximum response time in minutes")
    
    # Resolution metrics
    total_resolved = models.PositiveIntegerField(default=0, help_text="Total resolved emails")
    resolution_rate = models.FloatField(default=0.0, help_text="Resolution rate percentage")
    avg_resolution_time_hours = models.FloatField(default=0.0, help_text="Average resolution time in hours")
    
    # Customer satisfaction
    customer_satisfaction_score = models.FloatField(default=0.0, help_text="Customer satisfaction score (0-10)")
    positive_feedback_count = models.PositiveIntegerField(default=0, help_text="Positive feedback count")
    negative_feedback_count = models.PositiveIntegerField(default=0, help_text="Negative feedback count")
    
    # Category breakdown
    category_breakdown = models.JSONField(default=dict, help_text="Email category breakdown")
    priority_breakdown = models.JSONField(default=dict, help_text="Priority breakdown")
    sentiment_breakdown = models.JSONField(default=dict, help_text="Sentiment breakdown")
    
    # Performance metrics
    emails_per_hour = models.FloatField(default=0.0, help_text="Average emails per hour")
    peak_hour = models.TimeField(null=True, blank=True, help_text="Peak email hour")
    busiest_day = models.CharField(max_length=20, blank=True, help_text="Busiest day of week")
    
    # SLA metrics
    sla_met_count = models.PositiveIntegerField(default=0, help_text="SLA met count")
    sla_missed_count = models.PositiveIntegerField(default=0, help_text="SLA missed count")
    sla_compliance_rate = models.FloatField(default=0.0, help_text="SLA compliance rate percentage")
    
    class Meta:
        db_table = 'email_integration_analytics'
        ordering = ['-date', 'period_type']
        unique_together = ['date', 'period_type']
        indexes = [
            models.Index(fields=['date', 'period_type']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"Analytics - {self.date} ({self.get_period_type_display()})"


class EmailIntegration(BaseModel):
    """Third-party email integrations"""
    
    INTEGRATION_TYPE_CHOICES = [
        ('crm', 'CRM System'),
        ('helpdesk', 'Helpdesk System'),
        ('calendar', 'Calendar System'),
        ('slack', 'Slack'),
        ('teams', 'Microsoft Teams'),
        ('zapier', 'Zapier'),
        ('webhook', 'Custom Webhook'),
        ('api', 'Custom API'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error'),
        ('pending', 'Pending'),
    ]
    
    name = models.CharField(max_length=100, help_text="Integration name")
    description = models.TextField(blank=True, help_text="Integration description")
    integration_type = models.CharField(max_length=50, choices=INTEGRATION_TYPE_CHOICES, help_text="Integration type")
    
    # Configuration
    config = models.JSONField(help_text="Integration configuration")
    credentials = models.JSONField(default=dict, help_text="Encrypted credentials")
    
    # Status and health
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_active = models.BooleanField(default=True, help_text="Integration is active")
    last_sync = models.DateTimeField(null=True, blank=True, help_text="Last successful sync")
    last_error = models.TextField(blank=True, help_text="Last error message")
    error_count = models.PositiveIntegerField(default=0, help_text="Error count")
    
    # Sync settings
    sync_interval_minutes = models.PositiveIntegerField(default=60, help_text="Sync interval in minutes")
    auto_sync = models.BooleanField(default=True, help_text="Enable automatic sync")
    sync_direction = models.CharField(
        max_length=20,
        choices=[
            ('inbound', 'Inbound Only'),
            ('outbound', 'Outbound Only'),
            ('bidirectional', 'Bidirectional'),
        ],
        default='bidirectional',
        help_text="Sync direction"
    )
    
    # Statistics
    total_syncs = models.PositiveIntegerField(default=0, help_text="Total sync operations")
    successful_syncs = models.PositiveIntegerField(default=0, help_text="Successful sync operations")
    failed_syncs = models.PositiveIntegerField(default=0, help_text="Failed sync operations")
    
    class Meta:
        db_table = 'email_integrations'
        ordering = ['name']
        indexes = [
            models.Index(fields=['integration_type', 'is_active']),
            models.Index(fields=['status', 'last_sync']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_integration_type_display()})"
    
    def increment_sync_count(self, success=True):
        """Increment sync count"""
        self.total_syncs += 1
        if success:
            self.successful_syncs += 1
            self.last_sync = timezone.now()
            self.error_count = 0
        else:
            self.failed_syncs += 1
            self.error_count += 1
        self.save(update_fields=['total_syncs', 'successful_syncs', 'failed_syncs', 'last_sync', 'error_count'])


class EmailAutomationLog(BaseModel):
    """Log of automation executions"""
    
    automation = models.ForeignKey(
        EmailAutomation,
        on_delete=models.CASCADE,
        related_name='execution_logs',
        help_text="Related automation"
    )
    
    # Execution details
    trigger_data = models.JSONField(help_text="Data that triggered the automation")
    execution_result = models.JSONField(default=dict, help_text="Execution result data")
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('success', 'Success'),
            ('failed', 'Failed'),
            ('partial', 'Partial Success'),
            ('skipped', 'Skipped'),
        ],
        help_text="Execution status"
    )
    
    # Timing
    started_at = models.DateTimeField(help_text="Execution start time")
    completed_at = models.DateTimeField(null=True, blank=True, help_text="Execution completion time")
    duration_seconds = models.FloatField(null=True, blank=True, help_text="Execution duration in seconds")
    
    # Error details
    error_message = models.TextField(blank=True, help_text="Error message if failed")
    error_traceback = models.TextField(blank=True, help_text="Error traceback if failed")
    
    # Related objects
    email_message = models.ForeignKey(
        'email_operations.EmailMessage',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='automation_logs',
        help_text="Related email message"
    )
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='automation_logs',
        help_text="Related customer"
    )
    
    class Meta:
        db_table = 'email_automation_logs'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['automation', 'started_at']),
            models.Index(fields=['status', 'started_at']),
            models.Index(fields=['started_at']),
        ]
    
    def __str__(self):
        return f"{self.automation.name} - {self.status} - {self.started_at}"


class EmailSLA(BaseModel):
    """Email Service Level Agreement definitions"""
    
    name = models.CharField(max_length=100, help_text="SLA name")
    description = models.TextField(blank=True, help_text="SLA description")
    
    # SLA conditions
    conditions = models.JSONField(help_text="Conditions that trigger this SLA")
    
    # Response time requirements
    first_response_minutes = models.PositiveIntegerField(help_text="First response time in minutes")
    resolution_hours = models.PositiveIntegerField(help_text="Resolution time in hours")
    
    # Escalation settings
    escalation_enabled = models.BooleanField(default=True, help_text="Enable escalation")
    escalation_minutes = models.PositiveIntegerField(null=True, blank=True, help_text="Escalation time in minutes")
    escalation_actions = models.JSONField(default=list, help_text="Escalation actions")
    
    # Status
    is_active = models.BooleanField(default=True, help_text="SLA is active")
    
    class Meta:
        db_table = 'email_slas'
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.first_response_minutes}min response)"


class EmailTemplateVariable(BaseModel):
    """Dynamic email template variables"""
    
    name = models.CharField(max_length=100, help_text="Variable name")
    description = models.TextField(blank=True, help_text="Variable description")
    
    # Variable configuration
    variable_type = models.CharField(
        max_length=50,
        choices=[
            ('customer', 'Customer Data'),
            ('policy', 'Policy Data'),
            ('system', 'System Data'),
            ('custom', 'Custom Data'),
        ],
        help_text="Variable type"
    )
    
    # Data source
    data_source = models.CharField(max_length=200, help_text="Data source path")
    default_value = models.TextField(blank=True, help_text="Default value if not found")
    
    # Formatting
    format_string = models.CharField(max_length=100, blank=True, help_text="Format string for value")
    
    class Meta:
        db_table = 'email_template_variables'
        ordering = ['name']
        indexes = [
            models.Index(fields=['variable_type']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_variable_type_display()})"
