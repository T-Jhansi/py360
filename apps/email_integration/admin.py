"""
Email Integration Admin Configuration
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    EmailWebhook, EmailAutomation, EmailIntegrationAnalytics, EmailIntegration,
    EmailAutomationLog, EmailSLA, EmailTemplateVariable
)


@admin.register(EmailWebhook)
class EmailWebhookAdmin(admin.ModelAdmin):
    """Admin for EmailWebhook"""
    
    list_display = [
        'webhook_id_short', 'provider', 'event_type', 'status', 'email_message_id_short',
        'received_at', 'processed_at', 'processing_attempts', 'ip_address'
    ]
    list_filter = ['provider', 'event_type', 'status', 'received_at']
    search_fields = ['webhook_id', 'email_message_id', 'ip_address']
    ordering = ['-received_at']
    readonly_fields = [
        'webhook_id', 'received_at', 'processed_at', 'processing_attempts',
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Webhook Information', {
            'fields': ('webhook_id', 'provider', 'event_type', 'status')
        }),
        ('Email Reference', {
            'fields': ('email_message_id', 'email_id')
        }),
        ('Webhook Data', {
            'fields': ('webhook_data', 'processed_data')
        }),
        ('Processing Status', {
            'fields': ('processed_at', 'processing_attempts', 'error_message')
        }),
        ('Security & Timing', {
            'fields': ('received_at', 'provider_timestamp', 'signature', 'ip_address')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def webhook_id_short(self, obj):
        """Display shortened webhook ID"""
        return str(obj.webhook_id)[:8] + '...'
    webhook_id_short.short_description = 'Webhook ID'
    
    def email_message_id_short(self, obj):
        """Display shortened email message ID"""
        if obj.email_message_id:
            return obj.email_message_id[:20] + '...' if len(obj.email_message_id) > 20 else obj.email_message_id
        return '-'
    email_message_id_short.short_description = 'Email ID'


@admin.register(EmailAutomation)
class EmailAutomationAdmin(admin.ModelAdmin):
    """Admin for EmailAutomation"""
    
    list_display = [
        'name', 'trigger_type', 'is_active', 'execution_count', 'success_rate_display',
        'last_executed_at', 'priority'
    ]
    list_filter = ['trigger_type', 'is_active', 'last_executed_at']
    search_fields = ['name', 'description']
    ordering = ['-priority', 'name']
    readonly_fields = [
        'execution_count', 'last_executed_at', 'success_count', 'failure_count',
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'trigger_type')
        }),
        ('Configuration', {
            'fields': ('trigger_conditions', 'actions')
        }),
        ('Status & Execution', {
            'fields': ('is_active', 'execution_count', 'last_executed_at', 'success_count', 'failure_count')
        }),
        ('Advanced Settings', {
            'fields': ('delay_seconds', 'max_executions', 'run_once_per_email', 'run_once_per_customer', 'priority')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def success_rate_display(self, obj):
        """Display success rate percentage"""
        if obj.execution_count > 0:
            rate = (obj.success_count / obj.execution_count) * 100
            color = 'green' if rate >= 80 else 'orange' if rate >= 60 else 'red'
            return format_html(
                '<span style="color: {};">{:.1f}%</span>',
                color, rate
            )
        return '-'
    success_rate_display.short_description = 'Success Rate'


@admin.register(EmailIntegrationAnalytics)
class EmailIntegrationAnalyticsAdmin(admin.ModelAdmin):
    """Admin for EmailIntegrationAnalytics"""
    
    list_display = [
        'date', 'period_type', 'total_emails_received', 'total_emails_sent',
        'avg_response_time_display', 'resolution_rate_display', 'sla_compliance_rate_display'
    ]
    list_filter = ['period_type', 'date']
    search_fields = ['date']
    ordering = ['-date']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Period Information', {
            'fields': ('date', 'period_type')
        }),
        ('Email Volume', {
            'fields': ('total_emails_received', 'total_emails_sent', 'total_emails_replied', 'total_emails_forwarded')
        }),
        ('Response Time Metrics', {
            'fields': ('avg_response_time_minutes', 'min_response_time_minutes', 'max_response_time_minutes')
        }),
        ('Resolution Metrics', {
            'fields': ('total_resolved', 'resolution_rate', 'avg_resolution_time_hours')
        }),
        ('Customer Satisfaction', {
            'fields': ('customer_satisfaction_score', 'positive_feedback_count', 'negative_feedback_count')
        }),
        ('Breakdowns', {
            'fields': ('category_breakdown', 'priority_breakdown', 'sentiment_breakdown')
        }),
        ('Performance Metrics', {
            'fields': ('emails_per_hour', 'peak_hour', 'busiest_day')
        }),
        ('SLA Metrics', {
            'fields': ('sla_met_count', 'sla_missed_count', 'sla_compliance_rate')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def avg_response_time_display(self, obj):
        """Display average response time"""
        if obj.avg_response_time_minutes > 0:
            if obj.avg_response_time_minutes < 60:
                return f"{obj.avg_response_time_minutes:.1f} min"
            else:
                hours = obj.avg_response_time_minutes / 60
                return f"{hours:.1f} hours"
        return '-'
    avg_response_time_display.short_description = 'Avg Response Time'
    
    def resolution_rate_display(self, obj):
        """Display resolution rate"""
        if obj.resolution_rate > 0:
            color = 'green' if obj.resolution_rate >= 80 else 'orange' if obj.resolution_rate >= 60 else 'red'
            return format_html(
                '<span style="color: {};">{:.1f}%</span>',
                color, obj.resolution_rate
            )
        return '-'
    resolution_rate_display.short_description = 'Resolution Rate'
    
    def sla_compliance_rate_display(self, obj):
        """Display SLA compliance rate"""
        if obj.sla_compliance_rate > 0:
            color = 'green' if obj.sla_compliance_rate >= 95 else 'orange' if obj.sla_compliance_rate >= 80 else 'red'
            return format_html(
                '<span style="color: {};">{:.1f}%</span>',
                color, obj.sla_compliance_rate
            )
        return '-'
    sla_compliance_rate_display.short_description = 'SLA Compliance'


@admin.register(EmailIntegration)
class EmailIntegrationAdmin(admin.ModelAdmin):
    """Admin for EmailIntegration"""
    
    list_display = [
        'name', 'integration_type', 'status', 'is_active', 'last_sync_display',
        'success_rate_display', 'error_count'
    ]
    list_filter = ['integration_type', 'status', 'is_active', 'auto_sync']
    search_fields = ['name', 'description']
    ordering = ['name']
    readonly_fields = [
        'last_sync', 'last_error', 'error_count', 'total_syncs',
        'successful_syncs', 'failed_syncs', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'integration_type')
        }),
        ('Configuration', {
            'fields': ('config', 'credentials')
        }),
        ('Status & Health', {
            'fields': ('status', 'is_active', 'last_sync', 'last_error', 'error_count')
        }),
        ('Sync Settings', {
            'fields': ('sync_interval_minutes', 'auto_sync', 'sync_direction')
        }),
        ('Statistics', {
            'fields': ('total_syncs', 'successful_syncs', 'failed_syncs')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def last_sync_display(self, obj):
        """Display last sync time"""
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
    last_sync_display.short_description = 'Last Sync'
    
    def success_rate_display(self, obj):
        """Display sync success rate"""
        if obj.total_syncs > 0:
            rate = (obj.successful_syncs / obj.total_syncs) * 100
            color = 'green' if rate >= 90 else 'orange' if rate >= 70 else 'red'
            return format_html(
                '<span style="color: {};">{:.1f}%</span>',
                color, rate
            )
        return '-'
    success_rate_display.short_description = 'Success Rate'


@admin.register(EmailAutomationLog)
class EmailAutomationLogAdmin(admin.ModelAdmin):
    """Admin for EmailAutomationLog"""
    
    list_display = [
        'automation_name', 'status', 'started_at', 'duration_display',
        'email_message_link', 'customer_link'
    ]
    list_filter = ['status', 'started_at', 'automation']
    search_fields = ['automation__name', 'error_message']
    ordering = ['-started_at']
    readonly_fields = [
        'started_at', 'completed_at', 'duration_seconds', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Execution Information', {
            'fields': ('automation', 'status', 'started_at', 'completed_at', 'duration_seconds')
        }),
        ('Data', {
            'fields': ('trigger_data', 'execution_result')
        }),
        ('Error Details', {
            'fields': ('error_message', 'error_traceback')
        }),
        ('Related Objects', {
            'fields': ('email_message', 'customer')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def automation_name(self, obj):
        """Display automation name"""
        return obj.automation.name
    automation_name.short_description = 'Automation'
    
    def duration_display(self, obj):
        """Display execution duration"""
        if obj.duration_seconds:
            if obj.duration_seconds < 60:
                return f"{obj.duration_seconds:.2f}s"
            elif obj.duration_seconds < 3600:
                minutes = obj.duration_seconds / 60
                return f"{minutes:.2f}m"
            else:
                hours = obj.duration_seconds / 3600
                return f"{hours:.2f}h"
        return '-'
    duration_display.short_description = 'Duration'
    
    def email_message_link(self, obj):
        """Link to email message"""
        if obj.email_message:
            url = reverse('admin:email_operations_emailmessage_change', args=[obj.email_message.id])
            return format_html('<a href="{}">{}</a>', url, obj.email_message.id)
        return '-'
    email_message_link.short_description = 'Email Message'
    
    def customer_link(self, obj):
        """Link to customer"""
        if obj.customer:
            url = reverse('admin:customers_customer_change', args=[obj.customer.id])
            return format_html('<a href="{}">{}</a>', url, obj.customer.full_name)
        return '-'
    customer_link.short_description = 'Customer'


@admin.register(EmailSLA)
class EmailSLAAdmin(admin.ModelAdmin):
    """Admin for EmailSLA"""
    
    list_display = [
        'name', 'first_response_display', 'resolution_display',
        'escalation_enabled', 'is_active'
    ]
    list_filter = ['is_active', 'escalation_enabled']
    search_fields = ['name', 'description']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('SLA Conditions', {
            'fields': ('conditions',)
        }),
        ('Response Time Requirements', {
            'fields': ('first_response_minutes', 'resolution_hours')
        }),
        ('Escalation Settings', {
            'fields': ('escalation_enabled', 'escalation_minutes', 'escalation_actions')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def first_response_display(self, obj):
        """Display first response time"""
        if obj.first_response_minutes < 60:
            return f"{obj.first_response_minutes} min"
        else:
            hours = obj.first_response_minutes / 60
            return f"{hours:.1f} hours"
    first_response_display.short_description = 'First Response'
    
    def resolution_display(self, obj):
        """Display resolution time"""
        return f"{obj.resolution_hours} hours"
    resolution_display.short_description = 'Resolution Time'


@admin.register(EmailTemplateVariable)
class EmailTemplateVariableAdmin(admin.ModelAdmin):
    """Admin for EmailTemplateVariable"""
    
    list_display = [
        'name', 'variable_type', 'data_source', 'default_value_short', 'format_string'
    ]
    list_filter = ['variable_type']
    search_fields = ['name', 'description', 'data_source']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'variable_type')
        }),
        ('Data Configuration', {
            'fields': ('data_source', 'default_value', 'format_string')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def default_value_short(self, obj):
        """Display shortened default value"""
        if obj.default_value:
            return obj.default_value[:50] + '...' if len(obj.default_value) > 50 else obj.default_value
        return '-'
    default_value_short.short_description = 'Default Value'


# Customize admin site
admin.site.site_header = "Email Integration Administration"
admin.site.site_title = "Email Integration Admin"
admin.site.index_title = "Email Integration Management"
