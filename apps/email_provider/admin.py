"""
Admin configuration for email_provider app
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    EmailProviderConfig, EmailProviderHealthLog, 
    EmailProviderUsageLog, EmailProviderTestResult
)


@admin.register(EmailProviderConfig)
class EmailProviderConfigAdmin(admin.ModelAdmin):
    """Admin for EmailProviderConfig"""
    
    list_display = [
        'name', 'provider_type', 'is_active', 'is_default', 'priority',
        'health_status_badge', 'usage_display', 'created_at'
    ]
    list_filter = [
        'provider_type', 'is_active', 'is_default', 'health_status',
        'created_at', 'updated_at'
    ]
    search_fields = ['name', 'from_email', 'smtp_host']
    ordering = ['priority', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'provider_type', 'is_active', 'is_default', 'priority')
        }),
        ('Email Settings', {
            'fields': ('from_email', 'from_name', 'reply_to')
        }),
        ('Rate Limits', {
            'fields': ('daily_limit', 'monthly_limit', 'rate_limit_per_minute')
        }),
        ('Health Status', {
            'fields': ('health_status', 'health_error_message', 'consecutive_failures', 'last_health_check'),
            'classes': ('collapse',)
        }),
        ('Usage Statistics', {
            'fields': ('emails_sent_today', 'emails_sent_this_month', 'total_emails_sent', 
                      'total_emails_failed', 'average_response_time'),
            'classes': ('collapse',)
        }),
        ('SendGrid Settings', {
            'fields': ('api_key', 'api_secret'),
            'classes': ('collapse',)
        }),
        ('AWS SES Settings', {
            'fields': ('access_key_id', 'secret_access_key', 'region'),
            'classes': ('collapse',)
        }),
        ('SMTP Settings', {
            'fields': ('smtp_host', 'smtp_port', 'smtp_username', 'smtp_password', 
                      'smtp_use_tls', 'smtp_use_ssl'),
            'classes': ('collapse',)
        }),
        ('Additional Settings', {
            'fields': ('additional_settings',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = [
        'health_status', 'health_error_message', 'consecutive_failures', 'last_health_check',
        'emails_sent_today', 'emails_sent_this_month', 'total_emails_sent',
        'total_emails_failed', 'average_response_time'
    ]
    
    def health_status_badge(self, obj):
        """Display health status as colored badge"""
        colors = {
            'healthy': 'green',
            'degraded': 'orange',
            'unhealthy': 'red',
            'unknown': 'gray'
        }
        color = colors.get(obj.health_status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            color, obj.get_health_status_display()
        )
    health_status_badge.short_description = 'Health Status'
    
    def usage_display(self, obj):
        """Display usage statistics"""
        daily_pct = (obj.emails_sent_today / obj.daily_limit * 100) if obj.daily_limit > 0 else 0
        monthly_pct = (obj.emails_sent_this_month / obj.monthly_limit * 100) if obj.monthly_limit > 0 else 0
        
        return format_html(
            'Daily: {}% ({} / {})<br>Monthly: {}% ({} / {})',
            round(daily_pct, 1), obj.emails_sent_today, obj.daily_limit,
            round(monthly_pct, 1), obj.emails_sent_this_month, obj.monthly_limit
        )
    usage_display.short_description = 'Usage'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('created_by')


@admin.register(EmailProviderHealthLog)
class EmailProviderHealthLogAdmin(admin.ModelAdmin):
    """Admin for EmailProviderHealthLog"""
    
    list_display = [
        'provider', 'status_badge', 'test_type', 'response_time', 'created_at'
    ]
    list_filter = [
        'status', 'test_type', 'provider', 'created_at'
    ]
    search_fields = ['provider__name', 'error_message']
    ordering = ['-created_at']
    
    readonly_fields = ['provider', 'status', 'response_time', 'error_message', 'test_type', 'created_at']
    
    def status_badge(self, obj):
        """Display status as colored badge"""
        colors = {
            'healthy': 'green',
            'degraded': 'orange',
            'unhealthy': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def has_add_permission(self, request):
        """Disable adding health logs manually"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing health logs"""
        return False


@admin.register(EmailProviderUsageLog)
class EmailProviderUsageLogAdmin(admin.ModelAdmin):
    """Admin for EmailProviderUsageLog"""
    
    list_display = [
        'provider', 'date', 'emails_sent', 'emails_failed', 'success_rate', 'total_response_time'
    ]
    list_filter = [
        'provider', 'date'
    ]
    search_fields = ['provider__name']
    ordering = ['-date']
    
    readonly_fields = ['provider', 'emails_sent', 'emails_failed', 'total_response_time', 'date']
    
    def success_rate(self, obj):
        """Calculate and display success rate"""
        total = obj.emails_sent + obj.emails_failed
        if total > 0:
            rate = (obj.emails_sent / total) * 100
            color = 'green' if rate >= 95 else 'orange' if rate >= 90 else 'red'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
                color, rate
            )
        return 'N/A'
    success_rate.short_description = 'Success Rate'
    
    def has_add_permission(self, request):
        """Disable adding usage logs manually"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing usage logs"""
        return False


@admin.register(EmailProviderTestResult)
class EmailProviderTestResultAdmin(admin.ModelAdmin):
    """Admin for EmailProviderTestResult"""
    
    list_display = [
        'provider', 'test_type', 'status_badge', 'response_time', 'created_at'
    ]
    list_filter = [
        'test_type', 'status', 'provider', 'created_at'
    ]
    search_fields = ['provider__name', 'message']
    ordering = ['-created_at']
    
    readonly_fields = [
        'provider', 'test_type', 'status', 'message', 'response_time', 
        'test_data', 'created_at'
    ]
    
    def status_badge(self, obj):
        """Display status as colored badge"""
        colors = {
            'success': 'green',
            'failed': 'red',
            'warning': 'orange'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def has_add_permission(self, request):
        """Disable adding test results manually"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing test results"""
        return False