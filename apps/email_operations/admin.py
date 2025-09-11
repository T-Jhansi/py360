"""
Admin configuration for Email Operations
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import EmailMessage, EmailQueue, EmailTracking, EmailDeliveryReport, EmailAnalytics


@admin.register(EmailMessage)
class EmailMessageAdmin(admin.ModelAdmin):
    """Admin interface for EmailMessage"""
    
    list_display = [
        'message_id_short', 'to_email', 'subject_short', 'status_colored', 
        'priority', 'provider_used', 'sent_at', 'created_at'
    ]
    list_filter = [
        'status', 'priority', 'provider_used', 'template', 'campaign_id', 
        'created_at', 'sent_at'
    ]
    search_fields = [
        'to_email', 'subject', 'campaign_id', 'tags', 'provider_message_id'
    ]
    readonly_fields = [
        'message_id', 'status', 'provider_used', 'provider_message_id',
        'sent_at', 'delivered_at', 'opened_at', 'clicked_at', 'open_count',
        'click_count', 'bounce_reason', 'error_message', 'retry_count',
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Email Details', {
            'fields': (
                'message_id', 'to_email', 'cc_emails', 'bcc_emails',
                'from_email', 'from_name', 'reply_to', 'subject'
            )
        }),
        ('Content', {
            'fields': ('html_content', 'text_content', 'template', 'template_context'),
            'classes': ('collapse',)
        }),
        ('Status & Tracking', {
            'fields': (
                'status', 'priority', 'provider_used', 'provider_message_id',
                'sent_at', 'delivered_at', 'opened_at', 'clicked_at',
                'open_count', 'click_count', 'bounce_reason'
            )
        }),
        ('Error Handling', {
            'fields': ('error_message', 'retry_count', 'max_retries'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('scheduled_at', 'campaign_id', 'tags', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def message_id_short(self, obj):
        """Display shortened message ID"""
        return str(obj.message_id)[:8] + '...'
    message_id_short.short_description = 'Message ID'
    
    def subject_short(self, obj):
        """Display shortened subject"""
        return obj.subject[:50] + '...' if len(obj.subject) > 50 else obj.subject
    subject_short.short_description = 'Subject'
    
    def status_colored(self, obj):
        """Display status with color coding"""
        colors = {
            'pending': '#ffc107',
            'queued': '#17a2b8',
            'sending': '#007bff',
            'sent': '#28a745',
            'delivered': '#20c997',
            'opened': '#6f42c1',
            'clicked': '#e83e8c',
            'bounced': '#dc3545',
            'failed': '#fd7e14',
            'cancelled': '#6c757d'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_colored.short_description = 'Status'
    
    def get_queryset(self, request):
        """Filter out deleted messages"""
        return super().get_queryset(request).filter(is_deleted=False)


@admin.register(EmailQueue)
class EmailQueueAdmin(admin.ModelAdmin):
    """Admin interface for EmailQueue"""
    
    list_display = [
        'name', 'status_colored', 'total_emails', 'processed_emails', 
        'success_rate', 'started_at', 'created_at'
    ]
    list_filter = ['status', 'created_at', 'started_at']
    search_fields = ['name', 'description']
    readonly_fields = [
        'status', 'total_emails', 'processed_emails', 'failed_emails',
        'success_rate', 'started_at', 'completed_at', 'estimated_completion',
        'error_message', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Queue Information', {
            'fields': ('name', 'description', 'status')
        }),
        ('Processing Settings', {
            'fields': ('batch_size', 'delay_between_batches', 'max_retries')
        }),
        ('Statistics', {
            'fields': (
                'total_emails', 'processed_emails', 'failed_emails', 'success_rate'
            )
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at', 'estimated_completion')
        }),
        ('Error Handling', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def status_colored(self, obj):
        """Display status with color coding"""
        colors = {
            'pending': '#ffc107',
            'processing': '#007bff',
            'completed': '#28a745',
            'failed': '#dc3545',
            'cancelled': '#6c757d'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_colored.short_description = 'Status'
    
    def get_queryset(self, request):
        """Filter out deleted queues"""
        return super().get_queryset(request).filter(is_deleted=False)


@admin.register(EmailTracking)
class EmailTrackingAdmin(admin.ModelAdmin):
    """Admin interface for EmailTracking"""
    
    list_display = [
        'email_link', 'event_type_colored', 'ip_address', 'event_timestamp'
    ]
    list_filter = [
        'event_type', 'event_timestamp', 'email__status', 'email__template'
    ]
    search_fields = [
        'email__to_email', 'email__subject', 'ip_address', 'clicked_url'
    ]
    readonly_fields = ['event_timestamp', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Event Details', {
            'fields': ('email', 'event_type', 'event_timestamp', 'event_data')
        }),
        ('Tracking Information', {
            'fields': ('ip_address', 'user_agent', 'referrer')
        }),
        ('Click Details', {
            'fields': ('clicked_url', 'link_text'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def email_link(self, obj):
        """Display email as a link"""
        url = reverse('admin:email_operations_emailmessage_change', args=[obj.email.id])
        return format_html('<a href="{}">{}</a>', url, obj.email.to_email)
    email_link.short_description = 'Email'
    
    def event_type_colored(self, obj):
        """Display event type with color coding"""
        colors = {
            'sent': '#28a745',
            'delivered': '#20c997',
            'opened': '#6f42c1',
            'clicked': '#e83e8c',
            'bounced': '#dc3545',
            'unsubscribed': '#fd7e14',
            'complained': '#dc3545'
        }
        color = colors.get(obj.event_type, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_event_type_display()
        )
    event_type_colored.short_description = 'Event Type'
    
    def get_queryset(self, request):
        """Filter out tracking for deleted emails"""
        return super().get_queryset(request).filter(email__is_deleted=False)


@admin.register(EmailDeliveryReport)
class EmailDeliveryReportAdmin(admin.ModelAdmin):
    """Admin interface for EmailDeliveryReport"""
    
    list_display = [
        'report_date', 'provider_name', 'total_sent', 'delivery_rate_colored',
        'open_rate_colored', 'click_rate_colored', 'success_rate_colored'
    ]
    list_filter = ['provider_name', 'report_date']
    search_fields = ['provider_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Report Information', {
            'fields': ('report_date', 'provider_name')
        }),
        ('Statistics', {
            'fields': (
                'total_sent', 'total_delivered', 'total_opened', 'total_clicked',
                'total_bounced', 'total_failed'
            )
        }),
        ('Rates', {
            'fields': (
                'delivery_rate', 'open_rate', 'click_rate', 'bounce_rate',
                'avg_response_time', 'success_rate'
            )
        }),
        ('Additional Data', {
            'fields': ('report_data',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def delivery_rate_colored(self, obj):
        """Display delivery rate with color coding"""
        color = '#28a745' if obj.delivery_rate >= 95 else '#ffc107' if obj.delivery_rate >= 90 else '#dc3545'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color, obj.delivery_rate
        )
    delivery_rate_colored.short_description = 'Delivery Rate'
    
    def open_rate_colored(self, obj):
        """Display open rate with color coding"""
        color = '#28a745' if obj.open_rate >= 20 else '#ffc107' if obj.open_rate >= 10 else '#dc3545'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color, obj.open_rate
        )
    open_rate_colored.short_description = 'Open Rate'
    
    def click_rate_colored(self, obj):
        """Display click rate with color coding"""
        color = '#28a745' if obj.click_rate >= 5 else '#ffc107' if obj.click_rate >= 2 else '#dc3545'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color, obj.click_rate
        )
    click_rate_colored.short_description = 'Click Rate'
    
    def success_rate_colored(self, obj):
        """Display success rate with color coding"""
        color = '#28a745' if obj.success_rate >= 90 else '#ffc107' if obj.success_rate >= 80 else '#dc3545'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color, obj.success_rate
        )
    success_rate_colored.short_description = 'Success Rate'


@admin.register(EmailAnalytics)
class EmailAnalyticsAdmin(admin.ModelAdmin):
    """Admin interface for EmailAnalytics"""
    
    list_display = [
        'period_display', 'template_name', 'campaign_id', 'total_sent',
        'open_rate_colored', 'click_rate_colored', 'click_to_open_rate_colored'
    ]
    list_filter = [
        'template', 'campaign_id', 'period_start', 'period_end'
    ]
    search_fields = [
        'template__name', 'campaign_id'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Analytics Period', {
            'fields': ('period_start', 'period_end', 'template', 'campaign_id')
        }),
        ('Performance Metrics', {
            'fields': (
                'total_sent', 'total_delivered', 'total_opened', 'total_clicked',
                'total_bounced', 'total_unsubscribed'
            )
        }),
        ('Rates', {
            'fields': (
                'delivery_rate', 'open_rate', 'click_rate', 'bounce_rate',
                'unsubscribe_rate', 'click_to_open_rate'
            )
        }),
        ('Engagement Metrics', {
            'fields': (
                'unique_opens', 'unique_clicks', 'avg_time_to_open', 'avg_time_to_click'
            )
        }),
        ('Insights', {
            'fields': ('insights',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def period_display(self, obj):
        """Display analytics period"""
        return f"{obj.period_start.date()} - {obj.period_end.date()}"
    period_display.short_description = 'Period'
    
    def template_name(self, obj):
        """Display template name"""
        return obj.template.name if obj.template else 'N/A'
    template_name.short_description = 'Template'
    
    def open_rate_colored(self, obj):
        """Display open rate with color coding"""
        color = '#28a745' if obj.open_rate >= 20 else '#ffc107' if obj.open_rate >= 10 else '#dc3545'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color, obj.open_rate
        )
    open_rate_colored.short_description = 'Open Rate'
    
    def click_rate_colored(self, obj):
        """Display click rate with color coding"""
        color = '#28a745' if obj.click_rate >= 5 else '#ffc107' if obj.click_rate >= 2 else '#dc3545'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color, obj.click_rate
        )
    click_rate_colored.short_description = 'Click Rate'
    
    def click_to_open_rate_colored(self, obj):
        """Display click-to-open rate with color coding"""
        color = '#28a745' if obj.click_to_open_rate >= 20 else '#ffc107' if obj.click_to_open_rate >= 10 else '#dc3545'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color, obj.click_to_open_rate
        )
    click_to_open_rate_colored.short_description = 'Click-to-Open Rate'
