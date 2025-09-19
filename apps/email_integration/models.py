from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class EmailWebhook(models.Model):
    """Webhook events from email providers"""
    
    PROVIDER_CHOICES = [
        ('sendgrid', 'SendGrid'),
        ('aws_ses', 'AWS SES'),
        ('mailgun', 'Mailgun'),
        ('postmark', 'Postmark'),
    ]
    
    EVENT_TYPES = [
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
        ('bounced', 'Bounced'),
        ('complained', 'Complained'),
        ('unsubscribed', 'Unsubscribed'),
        ('blocked', 'Blocked'),
        ('deferred', 'Deferred'),
        ('dropped', 'Dropped'),
        ('incoming', 'Incoming Email'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processed', 'Processed'),
        ('failed', 'Failed'),
        ('ignored', 'Ignored'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Webhook data
    raw_data = models.JSONField(default=dict, help_text="Raw webhook payload")
    processed_data = models.JSONField(default=dict, blank=True, help_text="Processed webhook data")
    
    # Email identification
    email_message_id = models.CharField(max_length=255, blank=True, null=True)
    provider_message_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Event details
    event_time = models.DateTimeField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    
    # Processing
    processing_notes = models.TextField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    retry_count = models.PositiveIntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'email_webhooks'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['provider', 'event_type']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['email_message_id', 'event_type']),
        ]
        verbose_name = 'Email Webhook'
        verbose_name_plural = 'Email Webhooks'
    
    def __str__(self):
        return f"{self.provider} - {self.get_event_type_display()} ({self.status})"


class EmailAutomation(models.Model):
    """Email automation rules and workflows"""
    
    TRIGGER_TYPES = [
        ('email_received', 'Email Received'),
        ('email_opened', 'Email Opened'),
        ('email_clicked', 'Email Clicked'),
        ('email_bounced', 'Email Bounced'),
        ('email_complained', 'Email Complained'),
        ('email_unsubscribed', 'Email Unsubscribed'),
        ('time_based', 'Time Based'),
        ('webhook', 'Webhook'),
        ('manual', 'Manual'),
    ]
    
    ACTION_TYPES = [
        ('send_email', 'Send Email'),
        ('reply_email', 'Reply to Email'),
        ('forward_email', 'Forward Email'),
        ('move_to_folder', 'Move to Folder'),
        ('add_tag', 'Add Tag'),
        ('assign_to_user', 'Assign to User'),
        ('create_task', 'Create Task'),
        ('update_crm', 'Update CRM'),
        ('webhook_call', 'Webhook Call'),
        ('delay', 'Delay'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('draft', 'Draft'),
        ('archived', 'Archived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    
    # Trigger configuration
    trigger_type = models.CharField(max_length=20, choices=TRIGGER_TYPES)
    trigger_conditions = models.JSONField(default=dict, help_text="Trigger conditions and filters")
    
    # Action configuration
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    action_config = models.JSONField(default=dict, help_text="Action configuration and parameters")
    
    # Settings
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_active = models.BooleanField(default=True)
    priority = models.PositiveIntegerField(default=0, help_text="Execution priority")
    
    # Execution settings
    max_executions = models.PositiveIntegerField(default=0, help_text="Maximum executions (0 = unlimited)")
    execution_count = models.PositiveIntegerField(default=0)
    last_executed = models.DateTimeField(blank=True, null=True)
    
    # Timing
    delay_seconds = models.PositiveIntegerField(default=0, help_text="Delay before execution in seconds")
    cooldown_seconds = models.PositiveIntegerField(default=0, help_text="Cooldown between executions")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_email_automations')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_email_automations')
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deleted_email_automations')
    
    class Meta:
        db_table = 'email_automations'
        ordering = ['-priority', 'name']
        verbose_name = 'Email Automation'
        verbose_name_plural = 'Email Automations'
    
    def __str__(self):
        return self.name
    
    def soft_delete(self):
        """Soft delete the automation"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.is_active = False
        self.save(update_fields=['is_deleted', 'deleted_at', 'is_active'])


class EmailAutomationLog(models.Model):
    """Log of automation executions"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    automation = models.ForeignKey(EmailAutomation, on_delete=models.CASCADE, related_name='logs')
    
    # Execution details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    trigger_data = models.JSONField(default=dict, help_text="Data that triggered the automation")
    execution_data = models.JSONField(default=dict, blank=True, help_text="Data used during execution")
    
    # Results
    result_data = models.JSONField(default=dict, blank=True, help_text="Execution results")
    error_message = models.TextField(blank=True, null=True)
    
    # Timing
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    duration_seconds = models.FloatField(blank=True, null=True, help_text="Execution duration in seconds")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    executed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='executed_email_automations')
    
    class Meta:
        db_table = 'email_automation_logs'
        ordering = ['-created_at']
        verbose_name = 'Email Automation Log'
        verbose_name_plural = 'Email Automation Logs'
    
    def __str__(self):
        return f"{self.automation.name} - {self.get_status_display()} ({self.created_at})"


class EmailIntegration(models.Model):
    """Third-party integrations for email system"""
    
    INTEGRATION_TYPES = [
        ('crm', 'CRM System'),
        ('helpdesk', 'Helpdesk System'),
        ('analytics', 'Analytics Platform'),
        ('marketing', 'Marketing Platform'),
        ('calendar', 'Calendar System'),
        ('storage', 'File Storage'),
        ('api', 'Custom API'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error'),
        ('pending', 'Pending'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    integration_type = models.CharField(max_length=20, choices=INTEGRATION_TYPES)
    description = models.TextField(blank=True, null=True)
    
    # Configuration
    api_endpoint = models.URLField(blank=True, null=True)
    api_key = models.TextField(blank=True, null=True, help_text="API key (encrypted)")
    api_secret = models.TextField(blank=True, null=True, help_text="API secret (encrypted)")
    configuration = models.JSONField(default=dict, help_text="Integration-specific configuration")
    
    # Status and health
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    last_sync = models.DateTimeField(blank=True, null=True)
    last_error = models.TextField(blank=True, null=True)
    error_count = models.PositiveIntegerField(default=0)
    
    # Sync settings
    sync_enabled = models.BooleanField(default=True)
    sync_interval = models.PositiveIntegerField(default=3600, help_text="Sync interval in seconds")
    auto_sync = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_email_integrations')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_email_integrations')
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deleted_email_integrations')
    
    class Meta:
        db_table = 'email_integrations'
        ordering = ['name']
        verbose_name = 'Email Integration'
        verbose_name_plural = 'Email Integrations'
    
    def __str__(self):
        return f"{self.name} ({self.get_integration_type_display()})"
    
    def soft_delete(self):
        """Soft delete the integration"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.status = 'inactive'
        self.save(update_fields=['is_deleted', 'deleted_at', 'status'])


class EmailSLA(models.Model):
    """Service Level Agreements for email operations"""
    
    SLA_TYPES = [
        ('response_time', 'Response Time'),
        ('resolution_time', 'Resolution Time'),
        ('delivery_time', 'Delivery Time'),
        ('availability', 'Availability'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    
    # SLA configuration
    sla_type = models.CharField(max_length=20, choices=SLA_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    target_value = models.PositiveIntegerField(help_text="Target value in minutes")
    warning_threshold = models.PositiveIntegerField(help_text="Warning threshold in minutes")
    
    # Conditions
    conditions = models.JSONField(default=dict, help_text="SLA conditions and filters")
    
    # Settings
    is_active = models.BooleanField(default=True)
    is_escalation_enabled = models.BooleanField(default=True)
    escalation_recipients = models.JSONField(default=list, help_text="List of escalation email addresses")
    
    # Statistics
    total_incidents = models.PositiveIntegerField(default=0)
    met_sla_count = models.PositiveIntegerField(default=0)
    breached_sla_count = models.PositiveIntegerField(default=0)
    warning_count = models.PositiveIntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_email_slas')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_email_slas')
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deleted_email_slas')
    
    class Meta:
        db_table = 'email_slas'
        ordering = ['priority', 'name']
        verbose_name = 'Email SLA'
        verbose_name_plural = 'Email SLAs'
    
    def __str__(self):
        return f"{self.name} ({self.get_priority_display()})"
    
    def soft_delete(self):
        """Soft delete the SLA"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.is_active = False
        self.save(update_fields=['is_deleted', 'deleted_at', 'is_active'])


class EmailTemplateVariable(models.Model):
    """Dynamic template variables for email templates"""
    
    VARIABLE_TYPES = [
        ('text', 'Text'),
        ('number', 'Number'),
        ('date', 'Date'),
        ('datetime', 'DateTime'),
        ('boolean', 'Boolean'),
        ('email', 'Email'),
        ('url', 'URL'),
        ('json', 'JSON'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    
    # Variable configuration
    variable_type = models.CharField(max_length=20, choices=VARIABLE_TYPES)
    default_value = models.TextField(blank=True, null=True)
    is_required = models.BooleanField(default=False)
    validation_rules = models.JSONField(default=dict, help_text="Validation rules for the variable")
    
    # Usage tracking
    usage_count = models.PositiveIntegerField(default=0)
    last_used = models.DateTimeField(blank=True, null=True)
    
    # Settings
    is_active = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False, help_text="System-defined variable")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_email_template_variables')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_email_template_variables')
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deleted_email_template_variables')
    
    class Meta:
        db_table = 'email_template_variables'
        ordering = ['name']
        verbose_name = 'Email Template Variable'
        verbose_name_plural = 'Email Template Variables'
    
    def __str__(self):
        return f"{{{{{self.name}}}}}"
    
    def soft_delete(self):
        """Soft delete the template variable"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.is_active = False
        self.save(update_fields=['is_deleted', 'deleted_at', 'is_active'])


class EmailIntegrationAnalytics(models.Model):
    """Analytics for email integration features"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Time period
    date = models.DateField()
    period_type = models.CharField(max_length=20, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ], default='daily')
    
    # Integration metrics
    webhook_events_received = models.PositiveIntegerField(default=0)
    webhook_events_processed = models.PositiveIntegerField(default=0)
    webhook_events_failed = models.PositiveIntegerField(default=0)
    
    automation_executions = models.PositiveIntegerField(default=0)
    automation_successes = models.PositiveIntegerField(default=0)
    automation_failures = models.PositiveIntegerField(default=0)
    
    integration_syncs = models.PositiveIntegerField(default=0)
    integration_successes = models.PositiveIntegerField(default=0)
    integration_failures = models.PositiveIntegerField(default=0)
    
    # Calculated metrics
    webhook_success_rate = models.FloatField(default=0.0)
    automation_success_rate = models.FloatField(default=0.0)
    integration_success_rate = models.FloatField(default=0.0)
    
    # Response times
    avg_webhook_processing_time = models.FloatField(default=0.0)
    avg_automation_execution_time = models.FloatField(default=0.0)
    avg_integration_sync_time = models.FloatField(default=0.0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'email_integration_analytics'
        ordering = ['-date']
        unique_together = ['date', 'period_type']
        verbose_name = 'Email Integration Analytics'
        verbose_name_plural = 'Email Integration Analytics'
    
    def __str__(self):
        return f"Integration Analytics - {self.date} ({self.period_type})"
    
    def calculate_rates(self):
        """Calculate success rates"""
        if self.webhook_events_received > 0:
            self.webhook_success_rate = (self.webhook_events_processed / self.webhook_events_received) * 100
        
        if self.automation_executions > 0:
            self.automation_success_rate = (self.automation_successes / self.automation_executions) * 100
        
        if self.integration_syncs > 0:
            self.integration_success_rate = (self.integration_successes / self.integration_syncs) * 100
        
        self.save(update_fields=[
            'webhook_success_rate', 'automation_success_rate', 'integration_success_rate'
        ])
