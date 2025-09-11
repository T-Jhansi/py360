from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import BaseModel
import json

User = get_user_model()


class EmailProviderConfig(BaseModel):
    """Extended configuration for email providers with specific settings"""
    
    PROVIDER_TYPE_CHOICES = [
        ('sendgrid', 'SendGrid'),
        ('aws_ses', 'AWS SES'),
        ('smtp', 'SMTP'),
        ('gmail_api', 'Gmail API'),
        ('outlook_api', 'Outlook API'),
    ]
    
    # Basic provider info
    name = models.CharField(max_length=255, help_text="Provider name e.g., 'SendGrid Primary', 'AWS SES Backup'")
    provider_type = models.CharField(max_length=50, choices=PROVIDER_TYPE_CHOICES)
    is_default = models.BooleanField(default=False, help_text="Whether this is the default provider")
    is_active = models.BooleanField(default=True, help_text="Whether this provider is currently active")
    priority = models.PositiveIntegerField(default=1, help_text="Priority order (1=highest)")
    
    # Provider-specific settings (encrypted)
    api_key = models.TextField(blank=True, help_text="Encrypted API key")
    api_secret = models.TextField(blank=True, help_text="Encrypted API secret")
    access_key_id = models.TextField(blank=True, help_text="Encrypted AWS Access Key ID")
    secret_access_key = models.TextField(blank=True, help_text="Encrypted AWS Secret Access Key")
    region = models.CharField(max_length=50, blank=True, help_text="AWS region for SES")
    
    # SMTP settings (encrypted)
    smtp_host = models.CharField(max_length=255, blank=True)
    smtp_port = models.PositiveIntegerField(default=587, validators=[MinValueValidator(1), MaxValueValidator(65535)])
    smtp_username = models.CharField(max_length=255, blank=True)
    smtp_password = models.TextField(blank=True, help_text="Encrypted SMTP password")
    smtp_use_tls = models.BooleanField(default=True)
    smtp_use_ssl = models.BooleanField(default=False)
    
    # Email settings
    from_email = models.EmailField(help_text="Default from email address")
    from_name = models.CharField(max_length=255, blank=True, help_text="Default from name")
    reply_to = models.EmailField(blank=True, help_text="Default reply-to email")
    
    # Rate limiting
    daily_limit = models.PositiveIntegerField(default=10000, help_text="Daily email limit")
    monthly_limit = models.PositiveIntegerField(default=100000, help_text="Monthly email limit")
    rate_limit_per_minute = models.PositiveIntegerField(default=100, help_text="Rate limit per minute")
    
    # Health monitoring
    last_health_check = models.DateTimeField(null=True, blank=True)
    health_status = models.CharField(max_length=20, choices=[
        ('healthy', 'Healthy'),
        ('degraded', 'Degraded'),
        ('unhealthy', 'Unhealthy'),
        ('unknown', 'Unknown'),
    ], default='unknown')
    health_error_message = models.TextField(blank=True)
    consecutive_failures = models.PositiveIntegerField(default=0)
    
    # Usage tracking
    emails_sent_today = models.PositiveIntegerField(default=0)
    emails_sent_this_month = models.PositiveIntegerField(default=0)
    last_reset_daily = models.DateField(auto_now_add=True)
    last_reset_monthly = models.DateField(auto_now_add=True)
    
    # Statistics
    total_emails_sent = models.PositiveIntegerField(default=0)
    total_emails_failed = models.PositiveIntegerField(default=0)
    average_response_time = models.FloatField(default=0.0, help_text="Average response time in seconds")
    
    # Additional settings as JSON
    additional_settings = models.JSONField(default=dict, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_email_providers')
    
    class Meta:
        db_table = 'email_provider_configs'
        ordering = ['priority', 'name']
        indexes = [
            models.Index(fields=['provider_type', 'is_active']),
            models.Index(fields=['is_default', 'is_active']),
            models.Index(fields=['health_status', 'priority']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['is_default'],
                condition=models.Q(is_default=True),
                name='unique_default_email_provider'
            )
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_provider_type_display()})"
    
    def save(self, *args, **kwargs):
        if self.is_default:
            EmailProviderConfig.objects.filter(
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
    
    def get_encrypted_credentials(self):
        """Get decrypted credentials for this provider"""
        from .utils import decrypt_credentials
        return decrypt_credentials(self)
    
    def update_health_status(self, status, error_message=''):
        """Update health status and track failures"""
        from django.utils import timezone
        self.health_status = status
        self.health_error_message = error_message
        self.last_health_check = timezone.now()
        
        if status == 'unhealthy':
            self.consecutive_failures += 1
        else:
            self.consecutive_failures = 0
        
        self.save(update_fields=['health_status', 'health_error_message', 'last_health_check', 'consecutive_failures'])
    
    def can_send_email(self):
        """Check if provider can send email based on limits and health"""
        if not self.is_active:
            return False, "Provider is inactive"
        
        if self.health_status == 'unhealthy':
            return False, f"Provider is unhealthy: {self.health_error_message}"
        
        if self.emails_sent_today >= self.daily_limit:
            return False, "Daily limit reached"
        
        if self.emails_sent_this_month >= self.monthly_limit:
            return False, "Monthly limit reached"
        
        return True, "OK"
    
    def soft_delete(self, user=None):
        """Soft delete the provider"""
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.is_active = False
        self.save()


class EmailProviderHealthLog(BaseModel):
    """Health check logs for email providers"""
    
    provider = models.ForeignKey(EmailProviderConfig, on_delete=models.CASCADE, related_name='health_logs')
    status = models.CharField(max_length=20, choices=[
        ('healthy', 'Healthy'),
        ('degraded', 'Degraded'),
        ('unhealthy', 'Unhealthy'),
    ])
    response_time = models.FloatField(help_text="Response time in seconds")
    error_message = models.TextField(blank=True)
    test_type = models.CharField(max_length=50, choices=[
        ('connection', 'Connection Test'),
        ('send_test', 'Send Test'),
        ('api_test', 'API Test'),
    ])
    
    class Meta:
        db_table = 'email_provider_health_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['provider', 'created_at']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.provider.name} - {self.status} ({self.test_type})"


class EmailProviderUsageLog(BaseModel):
    """Usage tracking for email providers"""
    
    provider = models.ForeignKey(EmailProviderConfig, on_delete=models.CASCADE, related_name='usage_logs')
    emails_sent = models.PositiveIntegerField(default=0)
    emails_failed = models.PositiveIntegerField(default=0)
    total_response_time = models.FloatField(default=0.0)
    date = models.DateField()
    
    class Meta:
        db_table = 'email_provider_usage_logs'
        ordering = ['-date']
        unique_together = ['provider', 'date']
        indexes = [
            models.Index(fields=['provider', 'date']),
        ]
    
    def __str__(self):
        return f"{self.provider.name} - {self.date} ({self.emails_sent} sent)"


class EmailProviderTestResult(BaseModel):
    """Test results for email provider validation"""
    
    provider = models.ForeignKey(EmailProviderConfig, on_delete=models.CASCADE, related_name='test_results')
    test_type = models.CharField(max_length=50, choices=[
        ('connection', 'Connection Test'),
        ('authentication', 'Authentication Test'),
        ('send_test', 'Send Test Email'),
        ('api_validation', 'API Validation'),
    ])
    status = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('warning', 'Warning'),
    ])
    message = models.TextField()
    response_time = models.FloatField(null=True, blank=True)
    test_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'email_provider_test_results'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['provider', 'test_type']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.provider.name} - {self.test_type} - {self.status}"