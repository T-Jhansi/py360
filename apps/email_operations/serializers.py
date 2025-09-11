from rest_framework import serializers
from .models import EmailMessage, EmailQueue, EmailTracking, EmailDeliveryReport, EmailAnalytics


class EmailMessageSerializer(serializers.ModelSerializer):
    """Serializer for EmailMessage"""
    
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)
    
    class Meta:
        model = EmailMessage
        fields = [
            'id', 'message_id', 'to_email', 'cc_emails', 'bcc_emails',
            'from_email', 'from_name', 'reply_to', 'subject', 'html_content',
            'text_content', 'template_id', 'template_name', 'template_variables',
            'priority', 'priority_display', 'status', 'status_display',
            'scheduled_at', 'sent_at', 'campaign_id', 'tags', 'provider_name',
            'provider_message_id', 'error_message', 'retry_count', 'max_retries',
            'created_at', 'updated_at', 'created_by', 'created_by_name',
            'updated_by', 'updated_by_name', 'is_deleted', 'deleted_at', 'deleted_by'
        ]
        read_only_fields = [
            'id', 'message_id', 'sent_at', 'provider_name', 'provider_message_id',
            'error_message', 'retry_count', 'created_at', 'updated_at',
            'created_by', 'updated_by', 'is_deleted', 'deleted_at', 'deleted_by'
        ]


class EmailMessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating EmailMessage"""
    
    class Meta:
        model = EmailMessage
        fields = [
            'to_email', 'cc_emails', 'bcc_emails', 'from_email', 'from_name',
            'reply_to', 'subject', 'html_content', 'text_content', 'template_id',
            'template_variables', 'priority', 'scheduled_at', 'campaign_id', 'tags'
        ]
    
    def create(self, validated_data):
        """Create a new email message"""
        import uuid
        validated_data['message_id'] = str(uuid.uuid4())
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class EmailMessageUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating EmailMessage"""
    
    class Meta:
        model = EmailMessage
        fields = [
            'to_email', 'cc_emails', 'bcc_emails', 'from_email', 'from_name',
            'reply_to', 'subject', 'html_content', 'text_content', 'template_id',
            'template_variables', 'priority', 'scheduled_at', 'campaign_id', 'tags'
        ]
    
    def update(self, instance, validated_data):
        """Update an email message"""
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class EmailQueueSerializer(serializers.ModelSerializer):
    """Serializer for EmailQueue"""
    
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    email_message_data = EmailMessageSerializer(source='email_message', read_only=True)
    
    class Meta:
        model = EmailQueue
        fields = [
            'id', 'email_message', 'email_message_data', 'priority', 'priority_display',
            'status', 'status_display', 'scheduled_for', 'processed_at', 'attempts',
            'max_attempts', 'error_message', 'last_error', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'processed_at', 'attempts', 'error_message', 'last_error',
            'created_at', 'updated_at'
        ]


class EmailTrackingSerializer(serializers.ModelSerializer):
    """Serializer for EmailTracking"""
    
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    email_message_subject = serializers.CharField(source='email_message.subject', read_only=True)
    email_message_to = serializers.CharField(source='email_message.to_email', read_only=True)
    
    class Meta:
        model = EmailTracking
        fields = [
            'id', 'email_message', 'email_message_subject', 'email_message_to',
            'event_type', 'event_type_display', 'event_data', 'ip_address',
            'user_agent', 'location', 'link_url', 'link_text', 'event_time'
        ]
        read_only_fields = ['id', 'event_time']


class EmailDeliveryReportSerializer(serializers.ModelSerializer):
    """Serializer for EmailDeliveryReport"""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    email_message_subject = serializers.CharField(source='email_message.subject', read_only=True)
    email_message_to = serializers.CharField(source='email_message.to_email', read_only=True)
    
    class Meta:
        model = EmailDeliveryReport
        fields = [
            'id', 'email_message', 'email_message_subject', 'email_message_to',
            'provider_name', 'provider_message_id', 'status', 'status_display',
            'status_message', 'response_time', 'raw_data', 'reported_at'
        ]
        read_only_fields = ['id', 'reported_at']


class EmailAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for EmailAnalytics"""
    
    period_type_display = serializers.CharField(source='get_period_type_display', read_only=True)
    
    class Meta:
        model = EmailAnalytics
        fields = [
            'id', 'date', 'period_type', 'period_type_display', 'campaign_id',
            'template_id', 'emails_sent', 'emails_delivered', 'emails_opened',
            'emails_clicked', 'emails_bounced', 'emails_complained',
            'emails_unsubscribed', 'delivery_rate', 'open_rate', 'click_rate',
            'bounce_rate', 'complaint_rate', 'unsubscribe_rate',
            'avg_response_time', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'delivery_rate', 'open_rate', 'click_rate', 'bounce_rate',
            'complaint_rate', 'unsubscribe_rate', 'created_at', 'updated_at'
        ]


class BulkEmailSerializer(serializers.Serializer):
    """Serializer for bulk email sending"""
    
    to_emails = serializers.ListField(
        child=serializers.EmailField(),
        help_text="List of recipient email addresses"
    )
    subject = serializers.CharField(max_length=500)
    html_content = serializers.CharField(required=False, allow_blank=True)
    text_content = serializers.CharField(required=False, allow_blank=True)
    template_id = serializers.UUIDField(required=False, allow_null=True)
    template_variables = serializers.DictField(
        child=serializers.CharField(),
        required=False,
        default=dict
    )
    from_email = serializers.EmailField(required=False)
    from_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    reply_to = serializers.EmailField(required=False, allow_blank=True)
    cc_emails = serializers.ListField(
        child=serializers.EmailField(),
        required=False,
        default=list
    )
    bcc_emails = serializers.ListField(
        child=serializers.EmailField(),
        required=False,
        default=list
    )
    priority = serializers.ChoiceField(
        choices=EmailMessage.PRIORITY_CHOICES,
        default='normal'
    )
    scheduled_at = serializers.DateTimeField(required=False, allow_null=True)
    campaign_id = serializers.CharField(max_length=100, required=False, allow_blank=True)
    tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )


class ScheduledEmailSerializer(serializers.Serializer):
    """Serializer for scheduling emails"""
    
    to_email = serializers.EmailField()
    subject = serializers.CharField(max_length=500)
    html_content = serializers.CharField(required=False, allow_blank=True)
    text_content = serializers.CharField(required=False, allow_blank=True)
    template_id = serializers.UUIDField(required=False, allow_null=True)
    template_variables = serializers.DictField(
        child=serializers.CharField(),
        required=False,
        default=dict
    )
    from_email = serializers.EmailField(required=False)
    from_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    reply_to = serializers.EmailField(required=False, allow_blank=True)
    cc_emails = serializers.ListField(
        child=serializers.EmailField(),
        required=False,
        default=list
    )
    bcc_emails = serializers.ListField(
        child=serializers.EmailField(),
        required=False,
        default=list
    )
    priority = serializers.ChoiceField(
        choices=EmailMessage.PRIORITY_CHOICES,
        default='normal'
    )
    scheduled_at = serializers.DateTimeField()
    campaign_id = serializers.CharField(max_length=100, required=False, allow_blank=True)
    tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )


class EmailStatsSerializer(serializers.Serializer):
    """Serializer for email statistics"""
    
    total_emails = serializers.IntegerField()
    sent_emails = serializers.IntegerField()
    delivered_emails = serializers.IntegerField()
    failed_emails = serializers.IntegerField()
    pending_emails = serializers.IntegerField()
    delivery_rate = serializers.FloatField()
    open_rate = serializers.FloatField()
    click_rate = serializers.FloatField()
    bounce_rate = serializers.FloatField()
    avg_response_time = serializers.FloatField()
    emails_by_status = serializers.DictField()
    emails_by_priority = serializers.DictField()
    emails_by_campaign = serializers.DictField()
    recent_activity = serializers.ListField()


class EmailCampaignStatsSerializer(serializers.Serializer):
    """Serializer for email campaign statistics"""
    
    campaign_id = serializers.CharField()
    campaign_name = serializers.CharField()
    total_emails = serializers.IntegerField()
    sent_emails = serializers.IntegerField()
    delivered_emails = serializers.IntegerField()
    opened_emails = serializers.IntegerField()
    clicked_emails = serializers.IntegerField()
    bounced_emails = serializers.IntegerField()
    complained_emails = serializers.IntegerField()
    unsubscribed_emails = serializers.IntegerField()
    delivery_rate = serializers.FloatField()
    open_rate = serializers.FloatField()
    click_rate = serializers.FloatField()
    bounce_rate = serializers.FloatField()
    complaint_rate = serializers.FloatField()
    unsubscribe_rate = serializers.FloatField()
    avg_response_time = serializers.FloatField()
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
