from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.core.models import BaseModel

User = get_user_model()

class CommunicationProvider(BaseModel):    
    CHANNEL_CHOICES = [
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
        ('sms', 'SMS'),
        ('call', 'Call')
    ]

    name = models.CharField(max_length=255, help_text="Provider name e.g., 'SendGrid Primary', 'Meta Business API'")
    channel = models.CharField(max_length=50, choices=CHANNEL_CHOICES, help_text="Communication channel type")
    is_default = models.BooleanField(default=False, help_text="Whether this is the default provider for this channel")
    is_active = models.BooleanField(default=True, help_text="Whether this provider is currently active")

    class Meta:
        db_table = 'communication_providers'
        ordering = ['channel', 'name']
        indexes = [
            models.Index(fields=['channel']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_default']),
            models.Index(fields=['created_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['channel', 'is_default'],
                condition=models.Q(is_default=True),
                name='unique_default_per_channel'
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.get_channel_display()})"

    def save(self, *args, **kwargs):
        if self.is_default:
            CommunicationProvider.objects.filter(
                channel=self.channel,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def soft_delete(self, user=None):
        """Override soft delete to also set is_active to False"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if user:
            self.deleted_by = user
        self.is_active = False
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by', 'is_active'])

    def restore(self, user=None):
        """Override restore to also set is_active to True"""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.is_active = True
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by', 'is_active'])
