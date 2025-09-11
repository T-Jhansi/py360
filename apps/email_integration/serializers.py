"""
Serializers for Email Integration API endpoints
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    EmailWebhook, EmailAutomation, EmailIntegrationAnalytics, EmailIntegration,
    EmailAutomationLog, EmailSLA, EmailTemplateVariable
)

User = get_user_model()


class EmailWebhookSerializer(serializers.ModelSerializer):
    """Serializer for EmailWebhook"""
    
    provider_display = serializers.CharField(source='get_provider_display', read_only=True)
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    time_ago = serializers.SerializerMethodField()
    processing_duration = serializers.SerializerMethodField()
    
    class Meta: 
        model = EmailWebhook
        fields = [
            'id', 'webhook_id', 'provider', 'provider_display', 'event_type', 'event_type_display',
            'webhook_data', 'processed_data', 'email_message_id', 'email_id',
            'status', 'status_display', 'processed_at', 'processing_attempts', 'error_message',
            'received_at', 'provider_timestamp', 'signature', 'ip_address',
            'time_ago', 'processing_duration', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'webhook_id', 'processed_at', 'processing_attempts', 'received_at',
            'created_at', 'updated_at'
        ]
    
    def get_time_ago(self, obj):
        """Get human-readable time ago"""
        from django.utils import timezone
        now = timezone.now()
        diff = now - obj.received_at
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "Just now"
    
    def get_processing_duration(self, obj):
        """Get processing duration if completed"""
        if obj.processed_at and obj.received_at:
            duration = obj.processed_at - obj.received_at
            return duration.total_seconds()
        return None


class EmailAutomationSerializer(serializers.ModelSerializer):
    """Serializer for EmailAutomation"""
    
    trigger_type_display = serializers.CharField(source='get_trigger_type_display', read_only=True)
    success_rate = serializers.SerializerMethodField()
    last_execution_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = EmailAutomation
        fields = [
            'id', 'name', 'description', 'trigger_type', 'trigger_type_display',
            'trigger_conditions', 'actions', 'is_active', 'execution_count',
            'last_executed_at', 'success_count', 'failure_count', 'delay_seconds',
            'max_executions', 'run_once_per_email', 'run_once_per_customer',
            'priority', 'success_rate', 'last_execution_ago', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'execution_count', 'last_executed_at', 'success_count', 'failure_count',
            'created_at', 'updated_at'
        ]
    
    def get_success_rate(self, obj):
        """Calculate success rate percentage"""
        if obj.execution_count > 0:
            return round((obj.success_count / obj.execution_count) * 100, 2)
        return 0.0
    
    def get_last_execution_ago(self, obj):
        """Get human-readable time since last execution"""
        if obj.last_executed_at:
            from django.utils import timezone
            now = timezone.now()
            diff = now - obj.last_executed_at
            
            if diff.days > 0:
                return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            else:
                return "Just now"
        return "Never"


class EmailIntegrationAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for EmailIntegrationAnalytics"""
    
    period_type_display = serializers.CharField(source='get_period_type_display', read_only=True)
    
    class Meta:
        model = EmailIntegrationAnalytics
        fields = [
            'id', 'date', 'period_type', 'period_type_display',
            'total_emails_received', 'total_emails_sent', 'total_emails_replied', 'total_emails_forwarded',
            'avg_response_time_minutes', 'min_response_time_minutes', 'max_response_time_minutes',
            'total_resolved', 'resolution_rate', 'avg_resolution_time_hours',
            'customer_satisfaction_score', 'positive_feedback_count', 'negative_feedback_count',
            'category_breakdown', 'priority_breakdown', 'sentiment_breakdown',
            'emails_per_hour', 'peak_hour', 'busiest_day',
            'sla_met_count', 'sla_missed_count', 'sla_compliance_rate',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class EmailIntegrationSerializer(serializers.ModelSerializer):
    """Serializer for EmailIntegration"""
    
    integration_type_display = serializers.CharField(source='get_integration_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    sync_direction_display = serializers.CharField(source='get_sync_direction_display', read_only=True)
    last_sync_ago = serializers.SerializerMethodField()
    success_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = EmailIntegration
        fields = [
            'id', 'name', 'description', 'integration_type', 'integration_type_display',
            'config', 'credentials', 'status', 'status_display', 'is_active',
            'last_sync', 'last_error', 'error_count', 'sync_interval_minutes',
            'auto_sync', 'sync_direction', 'sync_direction_display',
            'total_syncs', 'successful_syncs', 'failed_syncs',
            'last_sync_ago', 'success_rate', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'last_sync', 'last_error', 'error_count', 'total_syncs',
            'successful_syncs', 'failed_syncs', 'created_at', 'updated_at'
        ]
    
    def get_last_sync_ago(self, obj):
        """Get human-readable time since last sync"""
        if obj.last_sync:
            from django.utils import timezone
            now = timezone.now()
            diff = now - obj.last_sync
            
            if diff.days > 0:
                return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            else:
                return "Just now"
        return "Never"
    
    def get_success_rate(self, obj):
        """Calculate sync success rate percentage"""
        if obj.total_syncs > 0:
            return round((obj.successful_syncs / obj.total_syncs) * 100, 2)
        return 0.0


class EmailAutomationLogSerializer(serializers.ModelSerializer):
    """Serializer for EmailAutomationLog"""
    
    automation_name = serializers.CharField(source='automation.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    duration_display = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = EmailAutomationLog
        fields = [
            'id', 'automation', 'automation_name', 'trigger_data', 'execution_result',
            'status', 'status_display', 'started_at', 'completed_at', 'duration_seconds',
            'duration_display', 'error_message', 'error_traceback', 'email_message',
            'customer', 'time_ago', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'started_at', 'completed_at', 'duration_seconds', 'created_at', 'updated_at'
        ]
    
    def get_duration_display(self, obj):
        """Get human-readable duration"""
        if obj.duration_seconds:
            if obj.duration_seconds < 60:
                return f"{obj.duration_seconds:.2f} seconds"
            elif obj.duration_seconds < 3600:
                minutes = obj.duration_seconds / 60
                return f"{minutes:.2f} minutes"
            else:
                hours = obj.duration_seconds / 3600
                return f"{hours:.2f} hours"
        return None
    
    def get_time_ago(self, obj):
        """Get human-readable time ago"""
        from django.utils import timezone
        now = timezone.now()
        diff = now - obj.started_at
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "Just now"


class EmailSLASerializer(serializers.ModelSerializer):
    """Serializer for EmailSLA"""
    
    class Meta:
        model = EmailSLA
        fields = [
            'id', 'name', 'description', 'conditions', 'first_response_minutes',
            'resolution_hours', 'escalation_enabled', 'escalation_minutes',
            'escalation_actions', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class EmailTemplateVariableSerializer(serializers.ModelSerializer):
    """Serializer for EmailTemplateVariable"""
    
    variable_type_display = serializers.CharField(source='get_variable_type_display', read_only=True)
    
    class Meta:
        model = EmailTemplateVariable
        fields = [
            'id', 'name', 'description', 'variable_type', 'variable_type_display',
            'data_source', 'default_value', 'format_string', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class WebhookProcessSerializer(serializers.Serializer):
    """Serializer for processing webhooks"""
    
    webhook_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of webhook IDs to process"
    )
    force_reprocess = serializers.BooleanField(
        default=False,
        help_text="Force reprocess even if already processed"
    )


class AutomationExecuteSerializer(serializers.Serializer):
    """Serializer for executing automations"""
    
    automation_id = serializers.IntegerField(help_text="Automation ID to execute")
    trigger_data = serializers.JSONField(help_text="Data to trigger the automation")
    force_execute = serializers.BooleanField(
        default=False,
        help_text="Force execution even if conditions not met"
    )


class IntegrationSyncSerializer(serializers.Serializer):
    """Serializer for syncing integrations"""
    
    integration_id = serializers.IntegerField(help_text="Integration ID to sync")
    sync_direction = serializers.ChoiceField(
        choices=['inbound', 'outbound', 'bidirectional'],
        default='bidirectional',
        help_text="Sync direction"
    )
    force_sync = serializers.BooleanField(
        default=False,
        help_text="Force sync even if recently synced"
    )


class AnalyticsReportSerializer(serializers.Serializer):
    """Serializer for generating analytics reports"""
    
    start_date = serializers.DateField(help_text="Report start date")
    end_date = serializers.DateField(help_text="Report end date")
    period_type = serializers.ChoiceField(
        choices=['daily', 'weekly', 'monthly', 'yearly'],
        default='daily',
        help_text="Report period type"
    )
    include_breakdowns = serializers.BooleanField(
        default=True,
        help_text="Include category/priority/sentiment breakdowns"
    )
    include_sla_metrics = serializers.BooleanField(
        default=True,
        help_text="Include SLA compliance metrics"
    )


class DynamicTemplateSerializer(serializers.Serializer):
    """Serializer for creating dynamic email templates"""
    
    template_name = serializers.CharField(max_length=100, help_text="Template name")
    subject = serializers.CharField(max_length=500, help_text="Email subject with variables")
    html_content = serializers.CharField(help_text="HTML content with variables")
    text_content = serializers.CharField(help_text="Plain text content with variables")
    variables = serializers.ListField(
        child=serializers.CharField(),
        help_text="List of variable names used in template"
    )
    category = serializers.CharField(max_length=50, help_text="Template category")
    is_active = serializers.BooleanField(default=True, help_text="Template is active")


class EmailScheduleSerializer(serializers.Serializer):
    """Serializer for scheduling emails"""
    
    to_emails = serializers.ListField(
        child=serializers.EmailField(),
        help_text="Recipient email addresses"
    )
    subject = serializers.CharField(max_length=500, help_text="Email subject")
    html_content = serializers.CharField(help_text="HTML content")
    text_content = serializers.CharField(help_text="Plain text content")
    scheduled_at = serializers.DateTimeField(help_text="When to send the email")
    template_id = serializers.IntegerField(
        required=False,
        help_text="Template ID to use"
    )
    variables = serializers.JSONField(
        default=dict,
        help_text="Template variables"
    )


class EmailReminderSerializer(serializers.Serializer):
    """Serializer for email reminders"""
    
    email_message_id = serializers.IntegerField(help_text="Email message ID to set reminder for")
    reminder_type = serializers.ChoiceField(
        choices=['follow_up', 'escalation', 'custom'],
        help_text="Type of reminder"
    )
    reminder_at = serializers.DateTimeField(help_text="When to send reminder")
    message = serializers.CharField(
        required=False,
        help_text="Custom reminder message"
    )
    actions = serializers.ListField(
        child=serializers.CharField(),
        help_text="Actions to take when reminder triggers"
    )


class EmailSignatureSerializer(serializers.Serializer):
    """Serializer for email signatures"""
    
    name = serializers.CharField(max_length=100, help_text="Signature name")
    content = serializers.CharField(help_text="Signature content")
    is_html = serializers.BooleanField(default=True, help_text="Content is HTML")
    is_default = serializers.BooleanField(default=False, help_text="Default signature")
    user_id = serializers.IntegerField(
        required=False,
        help_text="User ID (if user-specific signature)"
    )
    department = serializers.CharField(
        max_length=100,
        required=False,
        help_text="Department (if department-specific signature)"
    )
