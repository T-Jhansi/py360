"""
Serializers for Email Operations API endpoints
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import EmailMessage, EmailQueue, EmailTracking, EmailDeliveryReport, EmailAnalytics

User = get_user_model()


class EmailMessageSerializer(serializers.ModelSerializer):
    """Serializer for EmailMessage"""
    
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True)
    
    class Meta:
        model = EmailMessage
        fields = [
            'id', 'message_id', 'to_email', 'cc_emails', 'bcc_emails',
            'from_email', 'from_name', 'reply_to', 'subject', 'html_content', 'text_content',
            'template', 'template_name', 'template_context', 'status', 'status_display',
            'priority', 'priority_display', 'provider_used', 'provider_message_id',
            'scheduled_at', 'sent_at', 'delivered_at', 'opened_at', 'clicked_at',
            'error_message', 'retry_count', 'max_retries', 'open_count', 'click_count',
            'bounce_reason', 'campaign_id', 'tags', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'message_id', 'status', 'provider_used', 'provider_message_id',
            'sent_at', 'delivered_at', 'opened_at', 'clicked_at', 'error_message',
            'retry_count', 'open_count', 'click_count', 'bounce_reason', 'created_at', 'updated_at'
        ]


class EmailMessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating EmailMessage"""
    
    class Meta:
        model = EmailMessage
        fields = [
            'to_email', 'cc_emails', 'bcc_emails', 'from_email', 'from_name', 'reply_to',
            'subject', 'html_content', 'text_content', 'template', 'template_context',
            'priority', 'scheduled_at', 'campaign_id', 'tags', 'max_retries'
        ]
    
    def validate_cc_emails(self, value):
        """Validate CC emails"""
        if not isinstance(value, list):
            raise serializers.ValidationError("CC emails must be a list.")
        for email in value:
            if not isinstance(email, str) or '@' not in email:
                raise serializers.ValidationError(f"Invalid email address: {email}")
        return value
    
    def validate_bcc_emails(self, value):
        """Validate BCC emails"""
        if not isinstance(value, list):
            raise serializers.ValidationError("BCC emails must be a list.")
        for email in value:
            if not isinstance(email, str) or '@' not in email:
                raise serializers.ValidationError(f"Invalid email address: {email}")
        return value
    
    def validate_template_context(self, value):
        """Validate template context"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Template context must be a dictionary.")
        return value


class EmailBulkSendSerializer(serializers.Serializer):
    """Serializer for bulk email sending"""
    
    recipients = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of recipients with their context"
    )
    template_id = serializers.IntegerField(help_text="Template ID to use")
    from_email = serializers.EmailField(help_text="Sender email address")
    from_name = serializers.CharField(max_length=200, required=False, help_text="Sender name")
    reply_to = serializers.EmailField(required=False, help_text="Reply-to email address")
    cc_emails = serializers.ListField(
        child=serializers.EmailField(),
        required=False,
        help_text="CC email addresses"
    )
    bcc_emails = serializers.ListField(
        child=serializers.EmailField(),
        required=False,
        help_text="BCC email addresses"
    )
    priority = serializers.ChoiceField(
        choices=EmailMessage.PRIORITY_CHOICES,
        default='normal',
        help_text="Email priority"
    )
    scheduled_at = serializers.DateTimeField(required=False, help_text="When to send emails")
    campaign_id = serializers.CharField(max_length=100, required=False, help_text="Campaign identifier")
    tags = serializers.CharField(max_length=500, required=False, help_text="Comma-separated tags")
    
    def validate_recipients(self, value):
        """Validate recipients list"""
        if not value:
            raise serializers.ValidationError("At least one recipient is required.")
        
        for recipient in value:
            if 'email' not in recipient:
                raise serializers.ValidationError("Each recipient must have an 'email' field.")
            if not isinstance(recipient.get('context', {}), dict):
                raise serializers.ValidationError("Recipient context must be a dictionary.")
        
        return value


class EmailScheduledSendSerializer(serializers.Serializer):
    """Serializer for scheduled email sending"""
    
    to_email = serializers.EmailField(help_text="Recipient email address")
    template_id = serializers.IntegerField(help_text="Template ID to use")
    context = serializers.JSONField(default=dict, help_text="Template context variables")
    from_email = serializers.EmailField(help_text="Sender email address")
    from_name = serializers.CharField(max_length=200, required=False, help_text="Sender name")
    reply_to = serializers.EmailField(required=False, help_text="Reply-to email address")
    cc_emails = serializers.ListField(
        child=serializers.EmailField(),
        required=False,
        help_text="CC email addresses"
    )
    bcc_emails = serializers.ListField(
        child=serializers.EmailField(),
        required=False,
        help_text="BCC email addresses"
    )
    priority = serializers.ChoiceField(
        choices=EmailMessage.PRIORITY_CHOICES,
        default='normal',
        help_text="Email priority"
    )
    scheduled_at = serializers.DateTimeField(help_text="When to send the email")
    campaign_id = serializers.CharField(max_length=100, required=False, help_text="Campaign identifier")
    tags = serializers.CharField(max_length=500, required=False, help_text="Comma-separated tags")
    
    def validate_context(self, value):
        """Validate context format"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Context must be a dictionary.")
        return value


class EmailQueueSerializer(serializers.ModelSerializer):
    """Serializer for EmailQueue"""
    
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = EmailQueue
        fields = [
            'id', 'name', 'description', 'status', 'status_display',
            'batch_size', 'delay_between_batches', 'max_retries',
            'total_emails', 'processed_emails', 'failed_emails', 'success_rate',
            'started_at', 'completed_at', 'estimated_completion', 'error_message',
            'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'total_emails', 'processed_emails', 'failed_emails',
            'success_rate', 'started_at', 'completed_at', 'estimated_completion',
            'error_message', 'created_at', 'updated_at'
        ]


class EmailQueueCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating EmailQueue"""
    
    class Meta:
        model = EmailQueue
        fields = [
            'name', 'description', 'batch_size', 'delay_between_batches', 'max_retries'
        ]


class EmailTrackingSerializer(serializers.ModelSerializer):
    """Serializer for EmailTracking"""
    
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    email_subject = serializers.CharField(source='email.subject', read_only=True)
    email_recipient = serializers.CharField(source='email.to_email', read_only=True)
    
    class Meta:
        model = EmailTracking
        fields = [
            'id', 'email', 'email_subject', 'email_recipient', 'event_type', 'event_type_display',
            'event_data', 'ip_address', 'user_agent', 'referrer', 'clicked_url', 'link_text',
            'event_timestamp', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class EmailDeliveryReportSerializer(serializers.ModelSerializer):
    """Serializer for EmailDeliveryReport"""
    
    class Meta:
        model = EmailDeliveryReport
        fields = [
            'id', 'report_date', 'provider_name', 'total_sent', 'total_delivered',
            'total_opened', 'total_clicked', 'total_bounced', 'total_failed',
            'delivery_rate', 'open_rate', 'click_rate', 'bounce_rate', 'avg_response_time',
            'success_rate', 'report_data', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class EmailAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for EmailAnalytics"""
    
    template_name = serializers.CharField(source='template.name', read_only=True)
    
    class Meta:
        model = EmailAnalytics
        fields = [
            'id', 'period_start', 'period_end', 'template', 'template_name', 'campaign_id',
            'total_sent', 'total_delivered', 'total_opened', 'total_clicked', 'total_bounced',
            'total_unsubscribed', 'delivery_rate', 'open_rate', 'click_rate', 'bounce_rate',
            'unsubscribe_rate', 'unique_opens', 'unique_clicks', 'click_to_open_rate',
            'avg_time_to_open', 'avg_time_to_click', 'insights', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class EmailStatusSerializer(serializers.Serializer):
    """Serializer for email status response"""
    
    message_id = serializers.UUIDField()
    status = serializers.CharField()
    status_display = serializers.CharField()
    sent_at = serializers.DateTimeField(allow_null=True)
    delivered_at = serializers.DateTimeField(allow_null=True)
    opened_at = serializers.DateTimeField(allow_null=True)
    clicked_at = serializers.DateTimeField(allow_null=True)
    open_count = serializers.IntegerField()
    click_count = serializers.IntegerField()
    error_message = serializers.CharField(allow_blank=True)
    provider_used = serializers.CharField(allow_blank=True)


class EmailTrackingDataSerializer(serializers.Serializer):
    """Serializer for email tracking data response"""
    
    message_id = serializers.UUIDField()
    total_events = serializers.IntegerField()
    events = EmailTrackingSerializer(many=True)
    open_tracking_url = serializers.URLField()
    click_tracking_base_url = serializers.URLField()


class EmailAnalyticsSummarySerializer(serializers.Serializer):
    """Serializer for email analytics summary"""
    
    period_start = serializers.DateTimeField()
    period_end = serializers.DateTimeField()
    total_emails_sent = serializers.IntegerField()
    total_emails_delivered = serializers.IntegerField()
    total_emails_opened = serializers.IntegerField()
    total_emails_clicked = serializers.IntegerField()
    overall_delivery_rate = serializers.FloatField()
    overall_open_rate = serializers.FloatField()
    overall_click_rate = serializers.FloatField()
    top_performing_templates = serializers.ListField()
    provider_performance = serializers.DictField()


class EmailQueueStatusSerializer(serializers.Serializer):
    """Serializer for email queue status"""
    
    total_queued = serializers.IntegerField()
    total_processing = serializers.IntegerField()
    total_completed = serializers.IntegerField()
    total_failed = serializers.IntegerField()
    avg_processing_time = serializers.FloatField()
    estimated_completion = serializers.DateTimeField(allow_null=True)


class EmailRetrySerializer(serializers.Serializer):
    """Serializer for email retry request"""
    
    message_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text="List of message IDs to retry"
    )
    force_retry = serializers.BooleanField(
        default=False,
        help_text="Force retry even if max retries exceeded"
    )
    
    def validate_message_ids(self, value):
        """Validate message IDs exist"""
        if not value:
            raise serializers.ValidationError("At least one message ID is required.")
        return value
