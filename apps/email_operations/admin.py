from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import EmailMessage, EmailQueue, EmailTracking, EmailDeliveryReport, EmailAnalytics


@admin.register(EmailMessage)
class EmailMessageAdmin(admin.ModelAdmin):
    list_display = [
        'subject', 'to_email', 'from_email', 'status', 'priority',
        'campaign_id', 'created_at', 'sent_at'
    ]
    list_filter = ['status', 'priority', 'campaign_id', 'created_at', 'sent_at']
    search_fields = ['subject', 'to_email', 'from_email', 'message_id']
    readonly_fields = [
        'id', 'message_id', 'sent_at', 'provider_name', 'provider_message_id',
        'error_message', 'retry_count', 'created_at', 'updated_at',
        'created_by', 'updated_by', 'is_deleted', 'deleted_at', 'deleted_by'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('subject', 'to_email', 'from_email', 'from_name', 'reply_to')
        }),
        ('Content', {
            'fields': ('html_content', 'text_content', 'template_id', 'template_name', 'template_variables')
        }),
        ('Settings', {
            'fields': ('priority', 'status', 'scheduled_at', 'campaign_id', 'tags')
        }),
        ('Provider Information', {
            'fields': ('provider_name', 'provider_message_id', 'error_message', 'retry_count', 'max_retries'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'message_id', 'created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
        ('Soft Delete', {
            'fields': ('is_deleted', 'deleted_at', 'deleted_by'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        """Filter out soft-deleted messages"""
        return super().get_queryset(request).filter(is_deleted=False)
    
    actions = ['resend_emails', 'cancel_emails']
    
    def resend_emails(self, request, queryset):
        """Resend selected emails"""
        count = 0
        for email in queryset.filter(status__in=['failed', 'bounced']):
            email.status = 'pending'
            email.retry_count = 0
            email.error_message = None
            email.save()
            count += 1
        
        self.message_user(request, f"{count} emails scheduled for resending.")
    resend_emails.short_description = "Resend selected emails"
    
    def cancel_emails(self, request, queryset):
        """Cancel selected emails"""
        count = queryset.filter(status__in=['pending', 'sending']).update(status='cancelled')
        self.message_user(request, f"{count} emails cancelled.")
    cancel_emails.short_description = "Cancel selected emails"


@admin.register(EmailQueue)
class EmailQueueAdmin(admin.ModelAdmin):
    list_display = [
        'email_message_subject', 'priority', 'status', 'scheduled_for',
        'attempts', 'max_attempts', 'created_at'
    ]
    list_filter = ['status', 'priority', 'scheduled_for', 'created_at']
    search_fields = ['email_message__subject', 'email_message__to_email']
    readonly_fields = [
        'id', 'processed_at', 'attempts', 'error_message', 'last_error',
        'created_at', 'updated_at'
    ]
    
    def email_message_subject(self, obj):
        """Display email message subject"""
        return obj.email_message.subject
    email_message_subject.short_description = 'Subject'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('email_message')


@admin.register(EmailTracking)
class EmailTrackingAdmin(admin.ModelAdmin):
    list_display = [
        'email_message_subject', 'event_type', 'ip_address', 'location',
        'link_url', 'event_time'
    ]
    list_filter = ['event_type', 'event_time']
    search_fields = ['email_message__subject', 'email_message__to_email', 'ip_address']
    readonly_fields = ['id', 'event_time']
    
    def email_message_subject(self, obj):
        """Display email message subject"""
        return obj.email_message.subject
    email_message_subject.short_description = 'Subject'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('email_message')


@admin.register(EmailDeliveryReport)
class EmailDeliveryReportAdmin(admin.ModelAdmin):
    list_display = [
        'email_message_subject', 'provider_name', 'status', 'response_time',
        'reported_at'
    ]
    list_filter = ['provider_name', 'status', 'reported_at']
    search_fields = ['email_message__subject', 'email_message__to_email', 'provider_message_id']
    readonly_fields = ['id', 'reported_at']
    
    def email_message_subject(self, obj):
        """Display email message subject"""
        return obj.email_message.subject
    email_message_subject.short_description = 'Subject'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('email_message')


@admin.register(EmailAnalytics)
class EmailAnalyticsAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'period_type', 'campaign_id', 'emails_sent', 'emails_delivered',
        'delivery_rate', 'open_rate', 'click_rate'
    ]
    list_filter = ['period_type', 'date', 'campaign_id']
    search_fields = ['campaign_id', 'template_id']
    readonly_fields = [
        'id', 'delivery_rate', 'open_rate', 'click_rate', 'bounce_rate',
        'complaint_rate', 'unsubscribe_rate', 'created_at', 'updated_at'
    ]
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).order_by('-date')
