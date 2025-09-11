"""
Serializers for Email Inbox API endpoints
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    EmailInboxMessage, EmailConversation, EmailFolder, EmailFilter,
    EmailAttachment, EmailSearchQuery
)

User = get_user_model()


class EmailFolderSerializer(serializers.ModelSerializer):
    """Serializer for EmailFolder"""
    
    folder_type_display = serializers.CharField(source='get_folder_type_display', read_only=True)
    full_path = serializers.CharField(source='get_full_path', read_only=True)
    message_count = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = EmailFolder
        fields = [
            'id', 'name', 'description', 'folder_type', 'folder_type_display',
            'parent_folder', 'color', 'icon', 'sort_order', 'is_system',
            'full_path', 'message_count', 'unread_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_message_count(self, obj):
        """Get total message count in folder"""
        return obj.messages.count()
    
    def get_unread_count(self, obj):
        """Get unread message count in folder"""
        return obj.messages.filter(status='unread').count()


class EmailAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for EmailAttachment"""
    
    size_display = serializers.SerializerMethodField()
    
    class Meta:
        model = EmailAttachment
        fields = [
            'id', 'message', 'filename', 'content_type', 'size_bytes', 'size_display',
            'file_path', 'file_url', 'is_safe', 'virus_scan_status', 'virus_scan_result',
            'checksum', 'description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_size_display(self, obj):
        """Get human-readable file size"""
        size = obj.size_bytes
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


class EmailInboxMessageSerializer(serializers.ModelSerializer):
    """Serializer for EmailInboxMessage"""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    sentiment_display = serializers.CharField(source='get_sentiment_display', read_only=True)
    folder_name = serializers.CharField(source='folder.name', read_only=True)
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    policy_number = serializers.CharField(source='policy.policy_number', read_only=True)
    attachments = EmailAttachmentSerializer(many=True, read_only=True)
    tags_list = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = EmailInboxMessage
        fields = [
            'id', 'message_id', 'thread_id', 'in_reply_to', 'references',
            'from_email', 'from_name', 'to_emails', 'cc_emails', 'bcc_emails', 'reply_to',
            'subject', 'html_content', 'text_content', 'status', 'status_display',
            'is_starred', 'is_important', 'is_spam', 'is_phishing',
            'category', 'subcategory', 'priority', 'priority_display',
            'sentiment', 'sentiment_display', 'confidence_score',
            'attachments', 'attachment_count', 'folder', 'folder_name', 'tags', 'tags_list',
            'received_at', 'processed_at', 'read_at', 'replied_at',
            'headers', 'size_bytes', 'source', 'source_message_id',
            'customer', 'customer_name', 'policy', 'policy_number',
            'time_ago', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'message_id', 'thread_id', 'processed_at', 'read_at', 'replied_at',
            'attachment_count', 'created_at', 'updated_at'
        ]
    
    def get_tags_list(self, obj):
        """Get tags as a list"""
        if obj.tags:
            return [tag.strip() for tag in obj.tags.split(',')]
        return []
    
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


class EmailInboxMessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating EmailInboxMessage"""
    
    class Meta:
        model = EmailInboxMessage
        fields = [
            'message_id', 'thread_id', 'in_reply_to', 'references',
            'from_email', 'from_name', 'to_emails', 'cc_emails', 'bcc_emails', 'reply_to',
            'subject', 'html_content', 'text_content', 'attachments',
            'headers', 'size_bytes', 'source', 'source_message_id',
            'received_at'
        ]


class EmailConversationSerializer(serializers.ModelSerializer):
    """Serializer for EmailConversation"""
    
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    sentiment_display = serializers.CharField(source='get_sentiment_display', read_only=True)
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    policy_number = serializers.CharField(source='policy.policy_number', read_only=True)
    time_ago = serializers.SerializerMethodField()
    participants_display = serializers.SerializerMethodField()
    
    class Meta:
        model = EmailConversation
        fields = [
            'id', 'thread_id', 'subject', 'participants', 'participants_display',
            'message_count', 'unread_count', 'is_resolved', 'is_archived', 'is_starred',
            'category', 'priority', 'priority_display', 'sentiment', 'sentiment_display',
            'started_at', 'last_message_at', 'last_activity_at',
            'customer', 'customer_name', 'policy', 'policy_number',
            'time_ago', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'thread_id', 'message_count', 'unread_count', 'started_at',
            'last_message_at', 'last_activity_at', 'created_at', 'updated_at'
        ]
    
    def get_time_ago(self, obj):
        """Get human-readable time ago"""
        from django.utils import timezone
        now = timezone.now()
        diff = now - obj.last_activity_at
        
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
    
    def get_participants_display(self, obj):
        """Get formatted participants list"""
        return ', '.join(obj.participants[:3]) + ('...' if len(obj.participants) > 3 else '')


class EmailFilterSerializer(serializers.ModelSerializer):
    """Serializer for EmailFilter"""
    
    filter_type_display = serializers.CharField(source='get_filter_type_display', read_only=True)
    
    class Meta:
        model = EmailFilter
        fields = [
            'id', 'name', 'description', 'filter_type', 'filter_type_display',
            'filter_rules', 'actions', 'is_active', 'apply_to_existing',
            'match_count', 'last_matched_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'match_count', 'last_matched_at', 'created_at', 'updated_at'
        ]


class EmailSearchQuerySerializer(serializers.ModelSerializer):
    """Serializer for EmailSearchQuery"""
    
    class Meta:
        model = EmailSearchQuery
        fields = [
            'id', 'name', 'description', 'query_string', 'search_params',
            'use_count', 'last_used_at', 'is_public', 'is_favorite',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'use_count', 'last_used_at', 'created_at', 'updated_at'
        ]


class EmailBulkActionSerializer(serializers.Serializer):
    """Serializer for bulk email actions"""
    
    ACTION_CHOICES = [
        ('mark_read', 'Mark as Read'),
        ('mark_unread', 'Mark as Unread'),
        ('star', 'Star'),
        ('unstar', 'Unstar'),
        ('archive', 'Archive'),
        ('unarchive', 'Unarchive'),
        ('delete', 'Delete'),
        ('move_to_folder', 'Move to Folder'),
        ('add_tag', 'Add Tag'),
        ('remove_tag', 'Remove Tag'),
        ('mark_important', 'Mark as Important'),
        ('mark_spam', 'Mark as Spam'),
    ]
    
    message_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of message IDs to perform action on"
    )
    action = serializers.ChoiceField(
        choices=ACTION_CHOICES,
        help_text="Action to perform"
    )
    folder_id = serializers.IntegerField(
        required=False,
        help_text="Folder ID for move action"
    )
    tag = serializers.CharField(
        required=False,
        help_text="Tag for add/remove tag actions"
    )
    
    def validate_message_ids(self, value):
        """Validate message IDs exist"""
        if not value:
            raise serializers.ValidationError("At least one message ID is required.")
        return value


class EmailSearchSerializer(serializers.Serializer):
    """Serializer for email search"""
    
    query = serializers.CharField(
        required=False,
        help_text="Search query string"
    )
    folder_id = serializers.IntegerField(
        required=False,
        help_text="Filter by folder ID"
    )
    status = serializers.ChoiceField(
        choices=EmailInboxMessage.STATUS_CHOICES,
        required=False,
        help_text="Filter by status"
    )
    category = serializers.CharField(
        required=False,
        help_text="Filter by category"
    )
    priority = serializers.ChoiceField(
        choices=EmailInboxMessage.PRIORITY_CHOICES,
        required=False,
        help_text="Filter by priority"
    )
    is_starred = serializers.BooleanField(
        required=False,
        help_text="Filter by starred status"
    )
    is_important = serializers.BooleanField(
        required=False,
        help_text="Filter by important status"
    )
    has_attachments = serializers.BooleanField(
        required=False,
        help_text="Filter by attachment presence"
    )
    from_email = serializers.EmailField(
        required=False,
        help_text="Filter by sender email"
    )
    to_email = serializers.EmailField(
        required=False,
        help_text="Filter by recipient email"
    )
    date_from = serializers.DateField(
        required=False,
        help_text="Filter from date"
    )
    date_to = serializers.DateField(
        required=False,
        help_text="Filter to date"
    )
    customer_id = serializers.IntegerField(
        required=False,
        help_text="Filter by customer ID"
    )
    policy_id = serializers.IntegerField(
        required=False,
        help_text="Filter by policy ID"
    )
    sort_by = serializers.ChoiceField(
        choices=[
            ('received_at', 'Received Date'),
            ('subject', 'Subject'),
            ('from_email', 'Sender'),
            ('priority', 'Priority'),
            ('status', 'Status'),
        ],
        default='received_at',
        help_text="Sort field"
    )
    sort_order = serializers.ChoiceField(
        choices=[('asc', 'Ascending'), ('desc', 'Descending')],
        default='desc',
        help_text="Sort order"
    )


class EmailReplySerializer(serializers.Serializer):
    """Serializer for email reply"""
    
    message_id = serializers.IntegerField(help_text="Original message ID to reply to")
    subject = serializers.CharField(help_text="Reply subject")
    html_content = serializers.CharField(help_text="Reply HTML content")
    text_content = serializers.CharField(
        required=False,
        help_text="Reply plain text content"
    )
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
    attachments = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        help_text="Reply attachments"
    )
    
    def validate_message_id(self, value):
        """Validate original message exists"""
        try:
            EmailInboxMessage.objects.get(id=value)
        except EmailInboxMessage.DoesNotExist:
            raise serializers.ValidationError("Original message not found.")
        return value


class EmailForwardSerializer(serializers.Serializer):
    """Serializer for email forward"""
    
    message_id = serializers.IntegerField(help_text="Original message ID to forward")
    to_emails = serializers.ListField(
        child=serializers.EmailField(),
        help_text="Forward to email addresses"
    )
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
    subject = serializers.CharField(
        required=False,
        help_text="Forward subject (optional)"
    )
    message = serializers.CharField(
        required=False,
        help_text="Additional message (optional)"
    )
    
    def validate_message_id(self, value):
        """Validate original message exists"""
        try:
            EmailInboxMessage.objects.get(id=value)
        except EmailInboxMessage.DoesNotExist:
            raise serializers.ValidationError("Original message not found.")
        return value


class EmailStatsSerializer(serializers.Serializer):
    """Serializer for email statistics"""
    
    total_emails = serializers.IntegerField()
    unread_emails = serializers.IntegerField()
    starred_emails = serializers.IntegerField()
    important_emails = serializers.IntegerField()
    spam_emails = serializers.IntegerField()
    emails_today = serializers.IntegerField()
    emails_this_week = serializers.IntegerField()
    emails_this_month = serializers.IntegerField()
    category_stats = serializers.DictField()
    priority_stats = serializers.DictField()
    sentiment_stats = serializers.DictField()
    folder_stats = serializers.DictField()
