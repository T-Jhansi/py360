from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    WhatsAppBusinessAccount,
    WhatsAppPhoneNumber,
    WhatsAppMessageTemplate,
    WhatsAppMessage,
    WhatsAppWebhookEvent,
    WhatsAppFlow,
    WhatsAppAccountHealthLog,
    WhatsAppAccountUsageLog,
)


@admin.register(WhatsAppBusinessAccount)
class WhatsAppBusinessAccountAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'waba_id', 'status', 'quality_rating', 'is_active', 
        'messages_sent_today', 'health_status', 'created_at'
    ]
    list_filter = [
        'status', 'quality_rating', 'is_active', 'health_status',
        'enable_auto_reply', 'use_knowledge_base', 'created_at'
    ]
    search_fields = ['name', 'waba_id', 'meta_business_account_id', 'business_name']
    readonly_fields = [
        'waba_id', 'messages_sent_today', 'messages_sent_this_month',
        'last_reset_daily', 'last_reset_monthly', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'waba_id', 'meta_business_account_id', 'app_id', 'app_secret')
        }),
        ('Access Credentials', {
            'fields': ('access_token', 'webhook_verify_token'),
            'classes': ('collapse',)
        }),
        ('Business Profile', {
            'fields': (
                'business_name', 'business_description', 'business_email',
                'business_vertical', 'business_address'
            )
        }),
        ('Bot Configuration', {
            'fields': (
                'enable_auto_reply', 'use_knowledge_base', 'greeting_message',
                'fallback_message', 'enable_business_hours', 'business_hours_start',
                'business_hours_end', 'business_timezone'
            )
        }),
        ('Status & Health', {
            'fields': ('status', 'quality_rating', 'health_status', 'last_health_check')
        }),
        ('Rate Limiting', {
            'fields': (
                'daily_limit', 'monthly_limit', 'rate_limit_per_minute',
                'messages_sent_today', 'messages_sent_this_month'
            )
        }),
        ('Configuration', {
            'fields': ('is_default', 'is_active', 'webhook_url', 'subscribed_webhook_events')
        }),
        ('Metadata', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at', 'is_deleted'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by', 'updated_by')
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(WhatsAppPhoneNumber)
class WhatsAppPhoneNumberAdmin(admin.ModelAdmin):
    list_display = [
        'display_phone_number', 'waba_account', 'status', 'is_primary',
        'quality_rating', 'messages_sent_today', 'created_at'
    ]
    list_filter = [
        'status', 'is_primary', 'is_active', 'quality_rating',
        'waba_account', 'created_at'
    ]
    search_fields = [
        'phone_number', 'display_phone_number', 'phone_number_id',
        'waba_account__name'
    ]
    readonly_fields = [
        'phone_number_id', 'messages_sent_today', 'messages_sent_this_month',
        'created_at', 'updated_at', 'verified_at'
    ]
    
    fieldsets = (
        ('Phone Number Details', {
            'fields': (
                'waba_account', 'phone_number_id', 'phone_number',
                'display_phone_number'
            )
        }),
        ('Status & Configuration', {
            'fields': ('status', 'is_primary', 'is_active', 'quality_rating')
        }),
        ('Usage Tracking', {
            'fields': ('messages_sent_today', 'messages_sent_this_month', 'last_message_sent')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'verified_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('waba_account')


@admin.register(WhatsAppMessageTemplate)
class WhatsAppMessageTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'waba_account', 'category', 'language', 'status',
        'usage_count', 'created_at'
    ]
    list_filter = [
        'status', 'category', 'language', 'waba_account', 'created_at'
    ]
    search_fields = [
        'name', 'body_text', 'waba_account__name', 'meta_template_id'
    ]
    readonly_fields = [
        'meta_template_id', 'usage_count', 'last_used', 'created_at',
        'updated_at', 'approved_at'
    ]
    
    fieldsets = (
        ('Template Information', {
            'fields': ('waba_account', 'name', 'category', 'language')
        }),
        ('Template Content', {
            'fields': ('header_text', 'body_text', 'footer_text', 'components')
        }),
        ('Approval Status', {
            'fields': ('status', 'meta_template_id', 'rejection_reason')
        }),
        ('Usage Tracking', {
            'fields': ('usage_count', 'last_used')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at', 'approved_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('waba_account', 'created_by')


@admin.register(WhatsAppMessage)
class WhatsAppMessageAdmin(admin.ModelAdmin):
    list_display = [
        'message_id', 'direction', 'message_type', 'to_phone_number',
        'status', 'created_at', 'waba_account'
    ]
    list_filter = [
        'direction', 'message_type', 'status', 'waba_account',
        'phone_number', 'created_at'
    ]
    search_fields = [
        'message_id', 'to_phone_number', 'from_phone_number',
        'waba_account__name', 'customer__first_name', 'customer__last_name'
    ]
    readonly_fields = [
        'message_id', 'created_at', 'sent_at', 'delivered_at', 'read_at'
    ]
    
    fieldsets = (
        ('Message Details', {
            'fields': (
                'message_id', 'direction', 'message_type', 'waba_account',
                'phone_number', 'template'
            )
        }),
        ('Recipients', {
            'fields': ('to_phone_number', 'from_phone_number')
        }),
        ('Content', {
            'fields': ('content', 'metadata')
        }),
        ('Status & Delivery', {
            'fields': ('status', 'error_code', 'error_message')
        }),
        ('Context', {
            'fields': ('campaign', 'customer')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'sent_at', 'delivered_at', 'read_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'waba_account', 'phone_number', 'template', 'campaign', 'customer'
        )


@admin.register(WhatsAppWebhookEvent)
class WhatsAppWebhookEventAdmin(admin.ModelAdmin):
    list_display = [
        'event_type', 'waba_account', 'processed', 'received_at'
    ]
    list_filter = [
        'event_type', 'processed', 'waba_account', 'received_at'
    ]
    search_fields = [
        'waba_account__name', 'event_type', 'processing_error'
    ]
    readonly_fields = [
        'received_at', 'processed_at'
    ]
    
    fieldsets = (
        ('Event Information', {
            'fields': ('event_type', 'waba_account', 'message')
        }),
        ('Processing Status', {
            'fields': ('processed', 'processing_error', 'processed_at')
        }),
        ('Raw Data', {
            'fields': ('raw_data',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('received_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('waba_account', 'message')


@admin.register(WhatsAppFlow)
class WhatsAppFlowAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'waba_account', 'status', 'is_active', 'usage_count', 'created_at'
    ]
    list_filter = [
        'status', 'is_active', 'waba_account', 'created_at'
    ]
    search_fields = [
        'name', 'description', 'waba_account__name'
    ]
    readonly_fields = [
        'usage_count', 'last_used', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Flow Information', {
            'fields': ('waba_account', 'name', 'description')
        }),
        ('Flow Configuration', {
            'fields': ('flow_json', 'status', 'is_active')
        }),
        ('Usage Tracking', {
            'fields': ('usage_count', 'last_used')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('waba_account', 'created_by')


@admin.register(WhatsAppAccountHealthLog)
class WhatsAppAccountHealthLogAdmin(admin.ModelAdmin):
    list_display = [
        'waba_account', 'health_status', 'checked_at'
    ]
    list_filter = [
        'health_status', 'waba_account', 'checked_at'
    ]
    search_fields = [
        'waba_account__name', 'error_message'
    ]
    readonly_fields = ['checked_at']
    
    fieldsets = (
        ('Health Check', {
            'fields': ('waba_account', 'health_status', 'error_message')
        }),
        ('Check Details', {
            'fields': ('check_details',),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('checked_at',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('waba_account')


@admin.register(WhatsAppAccountUsageLog)
class WhatsAppAccountUsageLogAdmin(admin.ModelAdmin):
    list_display = [
        'waba_account', 'date', 'messages_sent', 'messages_delivered',
        'messages_failed', 'messages_read'
    ]
    list_filter = [
        'waba_account', 'date', 'created_at'
    ]
    search_fields = ['waba_account__name']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Usage Information', {
            'fields': ('waba_account', 'date')
        }),
        ('Message Statistics', {
            'fields': (
                'messages_sent', 'messages_delivered', 'messages_failed', 'messages_read'
            )
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('waba_account')
