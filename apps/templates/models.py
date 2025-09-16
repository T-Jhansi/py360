from django.db import models
from apps.users.models import User 

class Template(models.Model):
    """Stores content templates used in campaigns (email, sms, whatsapp, etc.)"""

    TEMPLATE_TYPES = [
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
        ('sms', 'SMS'),
    ]

    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('marketing', 'Marketing'),
        ('notification', 'Notification'),
        ('reminder', 'Reminder'),
        ('confirmation', 'Confirmation'),
        ('welcome', 'Welcome'),
        ('renewal', 'Renewal'),
        ('payment', 'Payment'),
    ]

    TEMPLATE_TYPE_CHOICES = [
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
        ('sms', 'SMS'),
    ]

    name = models.CharField(max_length=100, unique=True)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPE_CHOICES, default='email')
    channel = models.CharField(max_length=20, choices=TEMPLATE_TYPES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    subject = models.CharField(max_length=200, blank=True, help_text="Used for email subject")
    content = models.TextField(help_text="Template body content (HTML or plain text)")
    variables = models.JSONField(default=list, blank=True, help_text="List of dynamic variables used in the template")
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'templates'
        ordering = ['-created_at']
        unique_together = ('name', 'channel')

    def __str__(self):
        return f"{self.name} ({self.channel})"
