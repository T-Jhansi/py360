"""
Email Inbox Admin Configuration
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    EmailInboxMessage, EmailConversation, EmailFolder, EmailFilter,
    EmailAttachment, EmailSearchQuery
)


@admin.register(EmailFolder)
class EmailFolderAdmin(admin.ModelAdmin):
    """Admin for EmailFolder"""
    
    list_display = [
        'name', 'folder_type', 'parent_folder', 'color_display', 
        'sort_order', 'is_system', 'message_count', 'created_at'
    ]
    list_filter = ['folder_type', 'is_system', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['sort_order', 'name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'folder_type', 'parent_folder')
        }),
        ('Display Settings', {
            'fields': ('color', 'icon', 'sort_order')
        }),
        ('System Settings', {
            'fields': ('is_system',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def color_display(self, obj):
        """Display color as a colored square"""
        if obj.color:
            return format_html(
                '<span style="display: inline-block; width: 20px; height: 20px; '
                'background-color: {}; border: 1px solid #ccc;"></span> {}',
                obj.color, obj.color
            )
        return '-'
    color_display.short_description = 'Color'
    
    def message_count(self, obj):
        """Display message count"""
        return obj.messages.count()
    message_count.short_description = 'Messages'


@admin.register(EmailInboxMessage)
class EmailInboxMessageAdmin(admin.ModelAdmin):
    """Admin for EmailInboxMessage"""
    
    list_display = [
        'subject_short', 'from_email', 'from_name', 'status', 'category', 
        'priority', 'is_starred', 'is_important', 'folder', 'received_at'
    ]
    list_filter = [
        'status', 'category', 'priority', 'sentiment', 'is_starred', 
        'is_important', 'is_spam', 'folder', 'received_at'
    ]
    search_fields = [
        'subject', 'from_email', 'from_name', 'html_content', 'text_content'
    ]
    ordering = ['-received_at']
    readonly_fields = [
        'message_id', 'thread_id', 'processed_at', 'read_at', 'replied_at',
        'attachment_count', 'size_bytes', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Email Information', {
            'fields': (
                'message_id', 'thread_id', 'in_reply_to', 'references'
            )
        }),
        ('Addresses', {
            'fields': (
                'from_email', 'from_name', 'to_emails', 'cc_emails', 
                'bcc_emails', 'reply_to'
            )
        }),
        ('Content', {
            'fields': ('subject', 'html_content', 'text_content')
        }),
        ('Status & Flags', {
            'fields': (
                'status', 'is_starred', 'is_important', 'is_spam', 'is_phishing'
            )
        }),
        ('Classification', {
            'fields': (
                'category', 'subcategory', 'priority', 'sentiment', 'confidence_score'
            )
        }),
        ('Organization', {
            'fields': ('folder', 'tags')
        }),
        ('Attachments', {
            'fields': ('attachments', 'attachment_count')
        }),
        ('Timing', {
            'fields': (
                'received_at', 'processed_at', 'read_at', 'replied_at'
            )
        }),
        ('Metadata', {
            'fields': (
                'headers', 'size_bytes', 'source', 'source_message_id'
            )
        }),
        ('Associations', {
            'fields': ('customer', 'policy')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def subject_short(self, obj):
        """Display shortened subject"""
        return obj.subject[:50] + '...' if len(obj.subject) > 50 else obj.subject
    subject_short.short_description = 'Subject'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related(
            'folder', 'customer', 'policy'
        )


@admin.register(EmailConversation)
class EmailConversationAdmin(admin.ModelAdmin):
    """Admin for EmailConversation"""
    
    list_display = [
        'subject_short', 'participants_display', 'message_count', 
        'unread_count', 'category', 'priority', 'is_resolved', 
        'last_activity_at'
    ]
    list_filter = [
        'category', 'priority', 'sentiment', 'is_resolved', 
        'is_archived', 'is_starred', 'last_activity_at'
    ]
    search_fields = ['subject', 'participants']
    ordering = ['-last_activity_at']
    readonly_fields = [
        'thread_id', 'message_count', 'unread_count', 'started_at',
        'last_message_at', 'last_activity_at', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Conversation Information', {
            'fields': ('thread_id', 'subject', 'participants')
        }),
        ('Statistics', {
            'fields': ('message_count', 'unread_count')
        }),
        ('Status', {
            'fields': ('is_resolved', 'is_archived', 'is_starred')
        }),
        ('Classification', {
            'fields': ('category', 'priority', 'sentiment')
        }),
        ('Timing', {
            'fields': ('started_at', 'last_message_at', 'last_activity_at')
        }),
        ('Associations', {
            'fields': ('customer', 'policy')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def subject_short(self, obj):
        """Display shortened subject"""
        return obj.subject[:50] + '...' if len(obj.subject) > 50 else obj.subject
    subject_short.short_description = 'Subject'
    
    def participants_display(self, obj):
        """Display participants"""
        return ', '.join(obj.participants[:3]) + ('...' if len(obj.participants) > 3 else '')
    participants_display.short_description = 'Participants'


@admin.register(EmailFilter)
class EmailFilterAdmin(admin.ModelAdmin):
    """Admin for EmailFilter"""
    
    list_display = [
        'name', 'filter_type', 'is_active', 'match_count', 
        'last_matched_at', 'created_at'
    ]
    list_filter = ['filter_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    readonly_fields = [
        'match_count', 'last_matched_at', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'filter_type')
        }),
        ('Filter Rules', {
            'fields': ('filter_rules',)
        }),
        ('Actions', {
            'fields': ('actions',)
        }),
        ('Settings', {
            'fields': ('is_active', 'apply_to_existing')
        }),
        ('Statistics', {
            'fields': ('match_count', 'last_matched_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EmailAttachment)
class EmailAttachmentAdmin(admin.ModelAdmin):
    """Admin for EmailAttachment"""
    
    list_display = [
        'filename', 'message_link', 'content_type', 'size_display', 
        'is_safe', 'virus_scan_status', 'created_at'
    ]
    list_filter = [
        'content_type', 'is_safe', 'virus_scan_status', 'created_at'
    ]
    search_fields = ['filename', 'description']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('File Information', {
            'fields': ('message', 'filename', 'content_type', 'size_bytes')
        }),
        ('Storage', {
            'fields': ('file_path', 'file_url')
        }),
        ('Security', {
            'fields': ('is_safe', 'virus_scan_status', 'virus_scan_result', 'checksum')
        }),
        ('Metadata', {
            'fields': ('description',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def message_link(self, obj):
        """Link to message"""
        url = reverse('admin:email_inbox_emailinboxmessage_change', args=[obj.message.id])
        return format_html('<a href="{}">{}</a>', url, obj.message.subject[:30])
    message_link.short_description = 'Message'
    
    def size_display(self, obj):
        """Display human-readable file size"""
        size = obj.size_bytes
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    size_display.short_description = 'Size'


@admin.register(EmailSearchQuery)
class EmailSearchQueryAdmin(admin.ModelAdmin):
    """Admin for EmailSearchQuery"""
    
    list_display = [
        'name', 'query_string_short', 'use_count', 'is_public', 
        'is_favorite', 'last_used_at', 'created_at'
    ]
    list_filter = ['is_public', 'is_favorite', 'created_at']
    search_fields = ['name', 'description', 'query_string']
    ordering = ['-last_used_at', 'name']
    readonly_fields = [
        'use_count', 'last_used_at', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description')
        }),
        ('Query', {
            'fields': ('query_string', 'search_params')
        }),
        ('Statistics', {
            'fields': ('use_count', 'last_used_at')
        }),
        ('Sharing', {
            'fields': ('is_public', 'is_favorite')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def query_string_short(self, obj):
        """Display shortened query string"""
        return obj.query_string[:50] + '...' if len(obj.query_string) > 50 else obj.query_string
    query_string_short.short_description = 'Query'


# Customize admin site
admin.site.site_header = "Email Inbox Administration"
admin.site.site_title = "Email Inbox Admin"
admin.site.index_title = "Email Inbox Management"
