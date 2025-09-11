from rest_framework import serializers
from .models import (
    EmailWebhook, EmailAutomation, EmailAutomationLog, EmailIntegration,
    EmailSLA, EmailTemplateVariable, EmailIntegrationAnalytics
)


class EmailWebhookSerializer(serializers.ModelSerializer):
    """Serializer for EmailWebhook"""
    
    provider_display = serializers.CharField(source='get_provider_display', read_only=True)
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = EmailWebhook
        fields = [
            'id', 'provider', 'provider_display', 'event_type', 'event_type_display',
            'status', 'status_display', 'raw_data', 'processed_data',
            'email_message_id', 'provider_message_id', 'event_time',
            'ip_address', 'user_agent', 'processing_notes', 'error_message',
            'retry_count', 'created_at', 'processed_at'
        ]
        read_only_fields = [
            'id', 'processed_data', 'processing_notes', 'error_message',
            'retry_count', 'created_at', 'processed_at'
        ]


class EmailAutomationSerializer(serializers.ModelSerializer):
    """Serializer for EmailAutomation"""
    
    trigger_type_display = serializers.CharField(source='get_trigger_type_display', read_only=True)
    action_type_display = serializers.CharField(source='get_action_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)
    
    class Meta:
        model = EmailAutomation
        fields = [
            'id', 'name', 'description', 'trigger_type', 'trigger_type_display',
            'trigger_conditions', 'action_type', 'action_type_display',
            'action_config', 'status', 'status_display', 'is_active', 'priority',
            'max_executions', 'execution_count', 'last_executed', 'delay_seconds',
            'cooldown_seconds', 'created_at', 'updated_at', 'created_by',
            'created_by_name', 'updated_by', 'updated_by_name', 'is_deleted',
            'deleted_at', 'deleted_by'
        ]
        read_only_fields = [
            'id', 'execution_count', 'last_executed', 'created_at', 'updated_at',
            'created_by', 'updated_by', 'is_deleted', 'deleted_at', 'deleted_by'
        ]
    
    def create(self, validated_data):
        """Set created_by when creating a new automation"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Set updated_by when updating an automation"""
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class EmailAutomationLogSerializer(serializers.ModelSerializer):
    """Serializer for EmailAutomationLog"""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    automation_name = serializers.CharField(source='automation.name', read_only=True)
    executed_by_name = serializers.CharField(source='executed_by.get_full_name', read_only=True)
    
    class Meta:
        model = EmailAutomationLog
        fields = [
            'id', 'automation', 'automation_name', 'status', 'status_display',
            'trigger_data', 'execution_data', 'result_data', 'error_message',
            'started_at', 'completed_at', 'duration_seconds', 'created_at',
            'executed_by', 'executed_by_name'
        ]
        read_only_fields = [
            'id', 'started_at', 'completed_at', 'duration_seconds', 'created_at',
            'executed_by'
        ]


class EmailIntegrationSerializer(serializers.ModelSerializer):
    """Serializer for EmailIntegration"""
    
    integration_type_display = serializers.CharField(source='get_integration_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)
    
    class Meta:
        model = EmailIntegration
        fields = [
            'id', 'name', 'integration_type', 'integration_type_display',
            'description', 'api_endpoint', 'api_key', 'api_secret',
            'configuration', 'status', 'status_display', 'last_sync',
            'last_error', 'error_count', 'sync_enabled', 'sync_interval',
            'auto_sync', 'created_at', 'updated_at', 'created_by',
            'created_by_name', 'updated_by', 'updated_by_name', 'is_deleted',
            'deleted_at', 'deleted_by'
        ]
        read_only_fields = [
            'id', 'last_sync', 'last_error', 'error_count', 'created_at',
            'updated_at', 'created_by', 'updated_by', 'is_deleted', 'deleted_at', 'deleted_by'
        ]
    
    def create(self, validated_data):
        """Set created_by when creating a new integration"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Set updated_by when updating an integration"""
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class EmailSLASerializer(serializers.ModelSerializer):
    """Serializer for EmailSLA"""
    
    sla_type_display = serializers.CharField(source='get_sla_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)
    
    class Meta:
        model = EmailSLA
        fields = [
            'id', 'name', 'description', 'sla_type', 'sla_type_display',
            'priority', 'priority_display', 'target_value', 'warning_threshold',
            'conditions', 'is_active', 'is_escalation_enabled',
            'escalation_recipients', 'total_incidents', 'met_sla_count',
            'breached_sla_count', 'warning_count', 'created_at', 'updated_at',
            'created_by', 'created_by_name', 'updated_by', 'updated_by_name',
            'is_deleted', 'deleted_at', 'deleted_by'
        ]
        read_only_fields = [
            'id', 'total_incidents', 'met_sla_count', 'breached_sla_count',
            'warning_count', 'created_at', 'updated_at', 'created_by',
            'updated_by', 'is_deleted', 'deleted_at', 'deleted_by'
        ]
    
    def create(self, validated_data):
        """Set created_by when creating a new SLA"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Set updated_by when updating an SLA"""
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class EmailTemplateVariableSerializer(serializers.ModelSerializer):
    """Serializer for EmailTemplateVariable"""
    
    variable_type_display = serializers.CharField(source='get_variable_type_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)
    
    class Meta:
        model = EmailTemplateVariable
        fields = [
            'id', 'name', 'display_name', 'description', 'variable_type',
            'variable_type_display', 'default_value', 'is_required',
            'validation_rules', 'usage_count', 'last_used', 'is_active',
            'is_system', 'created_at', 'updated_at', 'created_by',
            'created_by_name', 'updated_by', 'updated_by_name', 'is_deleted',
            'deleted_at', 'deleted_by'
        ]
        read_only_fields = [
            'id', 'usage_count', 'last_used', 'created_at', 'updated_at',
            'created_by', 'updated_by', 'is_deleted', 'deleted_at', 'deleted_by'
        ]
    
    def create(self, validated_data):
        """Set created_by when creating a new template variable"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Set updated_by when updating a template variable"""
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class EmailIntegrationAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for EmailIntegrationAnalytics"""
    
    period_type_display = serializers.CharField(source='get_period_type_display', read_only=True)
    
    class Meta:
        model = EmailIntegrationAnalytics
        fields = [
            'id', 'date', 'period_type', 'period_type_display',
            'webhook_events_received', 'webhook_events_processed', 'webhook_events_failed',
            'automation_executions', 'automation_successes', 'automation_failures',
            'integration_syncs', 'integration_successes', 'integration_failures',
            'webhook_success_rate', 'automation_success_rate', 'integration_success_rate',
            'avg_webhook_processing_time', 'avg_automation_execution_time',
            'avg_integration_sync_time', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'webhook_success_rate', 'automation_success_rate',
            'integration_success_rate', 'created_at', 'updated_at'
        ]


class WebhookProcessSerializer(serializers.Serializer):
    """Serializer for processing webhooks"""
    
    webhook_id = serializers.UUIDField()
    force_process = serializers.BooleanField(default=False)


class AutomationExecuteSerializer(serializers.Serializer):
    """Serializer for executing automations"""
    
    automation_id = serializers.UUIDField()
    trigger_data = serializers.DictField(default=dict)
    force_execute = serializers.BooleanField(default=False)


class IntegrationSyncSerializer(serializers.Serializer):
    """Serializer for syncing integrations"""
    
    integration_id = serializers.UUIDField()
    sync_type = serializers.ChoiceField(choices=[
        ('full', 'Full Sync'),
        ('incremental', 'Incremental Sync'),
        ('manual', 'Manual Sync'),
    ], default='incremental')
    force_sync = serializers.BooleanField(default=False)


class DynamicTemplateCreateSerializer(serializers.Serializer):
    """Serializer for creating dynamic templates"""
    
    template_name = serializers.CharField(max_length=200)
    subject_template = serializers.CharField(max_length=500)
    html_template = serializers.CharField()
    text_template = serializers.CharField(required=False, allow_blank=True)
    variables = serializers.ListField(
        child=serializers.CharField(),
        help_text="List of variable names used in the template"
    )
    category = serializers.CharField(max_length=100, required=False)
    tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )


class EmailScheduleSerializer(serializers.Serializer):
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
    scheduled_at = serializers.DateTimeField()
    priority = serializers.ChoiceField(
        choices=[('low', 'Low'), ('normal', 'Normal'), ('high', 'High'), ('urgent', 'Urgent')],
        default='normal'
    )
    campaign_id = serializers.CharField(max_length=100, required=False, allow_blank=True)
    tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )


class EmailReminderSerializer(serializers.Serializer):
    """Serializer for creating email reminders"""
    
    email_id = serializers.UUIDField()
    reminder_type = serializers.ChoiceField(choices=[
        ('follow_up', 'Follow Up'),
        ('escalation', 'Escalation'),
        ('deadline', 'Deadline'),
        ('custom', 'Custom'),
    ])
    reminder_message = serializers.CharField(required=False, allow_blank=True)
    scheduled_at = serializers.DateTimeField()
    priority = serializers.ChoiceField(
        choices=[('low', 'Low'), ('normal', 'Normal'), ('high', 'High'), ('urgent', 'Urgent')],
        default='normal'
    )
    assigned_to = serializers.UUIDField(required=False, allow_null=True)


class EmailSignatureSerializer(serializers.Serializer):
    """Serializer for email signatures"""
    
    name = serializers.CharField(max_length=100)
    html_content = serializers.CharField()
    text_content = serializers.CharField(required=False, allow_blank=True)
    is_default = serializers.BooleanField(default=False)
    is_active = serializers.BooleanField(default=True)
    user_id = serializers.UUIDField(required=False, allow_null=True)


class SLAStatisticsSerializer(serializers.Serializer):
    """Serializer for SLA statistics"""
    
    sla_id = serializers.UUIDField()
    sla_name = serializers.CharField()
    sla_type = serializers.CharField()
    priority = serializers.CharField()
    total_incidents = serializers.IntegerField()
    met_sla_count = serializers.IntegerField()
    breached_sla_count = serializers.IntegerField()
    warning_count = serializers.IntegerField()
    met_sla_percentage = serializers.FloatField()
    breached_sla_percentage = serializers.FloatField()
    warning_percentage = serializers.FloatField()
    avg_response_time = serializers.FloatField()
    avg_resolution_time = serializers.FloatField()
    last_incident = serializers.DateTimeField()
    last_breach = serializers.DateTimeField()


class IntegrationStatisticsSerializer(serializers.Serializer):
    """Serializer for integration statistics"""
    
    integration_id = serializers.UUIDField()
    integration_name = serializers.CharField()
    integration_type = serializers.CharField()
    status = serializers.CharField()
    total_syncs = serializers.IntegerField()
    successful_syncs = serializers.IntegerField()
    failed_syncs = serializers.IntegerField()
    success_rate = serializers.FloatField()
    avg_sync_time = serializers.FloatField()
    last_sync = serializers.DateTimeField()
    last_error = serializers.CharField()
    error_count = serializers.IntegerField()
