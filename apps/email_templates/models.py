"""
Email Templates Models
"""
from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import BaseModel
from django.utils import timezone

User = get_user_model()


class EmailTemplate(BaseModel):
    """Email template for reusable email content"""
    
    TEMPLATE_TYPES = [
        ('welcome', 'Welcome Email'),
        ('renewal_reminder', 'Renewal Reminder'),
        ('payment_confirmation', 'Payment Confirmation'),
        ('policy_update', 'Policy Update'),
        ('marketing', 'Marketing'),
        ('notification', 'Notification'),
        ('custom', 'Custom'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ]
    
    name = models.CharField(max_length=200, help_text="Template name")
    subject = models.CharField(max_length=500, help_text="Email subject line")
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPES, default='custom')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Content
    html_content = models.TextField(help_text="HTML email content")
    text_content = models.TextField(blank=True, help_text="Plain text version")
    
    # Template variables
    variables = models.JSONField(default=dict, blank=True, help_text="Available template variables")
    
    # Metadata
    description = models.TextField(blank=True, help_text="Template description")
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    
    # Usage tracking
    usage_count = models.PositiveIntegerField(default=0, help_text="Number of times used")
    last_used = models.DateTimeField(null=True, blank=True, help_text="Last time template was used")
    
    # Template settings
    is_default = models.BooleanField(default=False, help_text="Default template for this type")
    requires_approval = models.BooleanField(default=False, help_text="Requires approval before use")
    
    class Meta:
        db_table = 'email_templates'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['template_type', 'status']),
            models.Index(fields=['status', 'is_default']),
            models.Index(fields=['created_by', 'status']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"
    
    def increment_usage(self):
        """Increment usage count and update last used"""
        self.usage_count += 1
        self.last_used = timezone.now()
        self.save(update_fields=['usage_count', 'last_used'])
    
    def get_variables_list(self):
        """Get list of available variables"""
        if isinstance(self.variables, dict):
            return list(self.variables.keys())
        return []
    
    def render_content(self, context=None):
        """Render template with provided context"""
        if context is None:
            context = {}
        
        # Simple template rendering (can be enhanced with Jinja2 later)
        html_content = self.html_content
        text_content = self.text_content
        subject = self.subject
        
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"  # {{variable_name}}
            html_content = html_content.replace(placeholder, str(value))
            text_content = text_content.replace(placeholder, str(value))
            subject = subject.replace(placeholder, str(value))
        
        return {
            'subject': subject,
            'html_content': html_content,
            'text_content': text_content
        }


class EmailTemplateVersion(BaseModel):
    """Version history for email templates"""
    
    template = models.ForeignKey(EmailTemplate, on_delete=models.CASCADE, related_name='versions')
    version_number = models.PositiveIntegerField(help_text="Version number")
    
    # Content snapshot
    subject = models.CharField(max_length=500)
    html_content = models.TextField()
    text_content = models.TextField(blank=True)
    variables = models.JSONField(default=dict, blank=True)
    
    # Change tracking
    change_notes = models.TextField(blank=True, help_text="Notes about this version")
    is_current = models.BooleanField(default=False, help_text="Is this the current version")
    
    class Meta:
        db_table = 'email_template_versions'
        ordering = ['-version_number']
        unique_together = ['template', 'version_number']
        indexes = [
            models.Index(fields=['template', 'is_current']),
        ]
    
    def __str__(self):
        return f"{self.template.name} v{self.version_number}"


class EmailTemplateCategory(BaseModel):
    """Categories for organizing email templates"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#007bff', help_text="Hex color code")
    icon = models.CharField(max_length=50, blank=True, help_text="Icon class or name")
    sort_order = models.PositiveIntegerField(default=0, help_text="Sort order")
    
    class Meta:
        db_table = 'email_template_categories'
        ordering = ['sort_order', 'name']
        verbose_name_plural = 'Email Template Categories'
    
    def __str__(self):
        return self.name


class EmailTemplateTag(BaseModel):
    """Tags for email templates"""
    
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#6c757d', help_text="Hex color code")
    
    class Meta:
        db_table = 'email_template_tags'
        ordering = ['name']
    
    def __str__(self):
        return self.name
