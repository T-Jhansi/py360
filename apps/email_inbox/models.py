"""
Email Inbox Models
"""
from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import BaseModel
from django.utils import timezone
import uuid

User = get_user_model()


class EmailFolder(BaseModel):
    """Email folders for organizing inbox messages"""
    
    FOLDER_TYPES = [
        ('inbox', 'Inbox'),
        ('sent', 'Sent'),
        ('drafts', 'Drafts'),
        ('trash', 'Trash'),
        ('archive', 'Archive'),
        ('spam', 'Spam'),
        ('custom', 'Custom'),
    ]
    
    name = models.CharField(max_length=100, help_text="Folder name")
    description = models.TextField(blank=True, help_text="Folder description")
    folder_type = models.CharField(max_length=20, choices=FOLDER_TYPES, default='custom')
    parent_folder = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='subfolders',
        help_text="Parent folder for nested folders"
    )
    color = models.CharField(max_length=7, default='#007bff', help_text="Folder color in hex")
    icon = models.CharField(max_length=50, default='folder', help_text="Folder icon")
    sort_order = models.PositiveIntegerField(default=0, help_text="Sort order for display")
    is_system = models.BooleanField(default=False, help_text="System folder (cannot be deleted)")
    
    class Meta:
        db_table = 'email_folders'
        ordering = ['sort_order', 'name']
        unique_together = ['name', 'parent_folder']
        indexes = [
            models.Index(fields=['folder_type', 'is_system']),
            models.Index(fields=['parent_folder', 'sort_order']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_folder_type_display()})"
    
    def get_full_path(self):
        """Get full folder path including parent folders"""
        if self.parent_folder:
            return f"{self.parent_folder.get_full_path()}/{self.name}"
        return self.name


class EmailInboxMessage(BaseModel):
    """Incoming email messages"""
    
    STATUS_CHOICES = [
        ('unread', 'Unread'),
        ('read', 'Read'),
        ('replied', 'Replied'),
        ('forwarded', 'Forwarded'),
        ('archived', 'Archived'),
        ('deleted', 'Deleted'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    SENTIMENT_CHOICES = [
        ('positive', 'Positive'),
        ('neutral', 'Neutral'),
        ('negative', 'Negative'),
        ('unknown', 'Unknown'),
    ]
    
    # Email identification
    message_id = models.CharField(max_length=500, unique=True, help_text="Unique message ID")
    thread_id = models.CharField(max_length=500, blank=True, help_text="Thread ID for conversation grouping")
    in_reply_to = models.CharField(max_length=500, blank=True, help_text="Message ID this is replying to")
    references = models.TextField(blank=True, help_text="Reference message IDs")
    
    # Email addresses
    from_email = models.EmailField(help_text="Sender email address")
    from_name = models.CharField(max_length=200, blank=True, help_text="Sender name")
    to_emails = models.JSONField(default=list, help_text="Recipient email addresses")
    cc_emails = models.JSONField(default=list, blank=True, help_text="CC email addresses")
    bcc_emails = models.JSONField(default=list, blank=True, help_text="BCC email addresses")
    reply_to = models.EmailField(blank=True, help_text="Reply-to email address")
    
    # Email content
    subject = models.CharField(max_length=500, help_text="Email subject")
    html_content = models.TextField(help_text="HTML email content")
    text_content = models.TextField(blank=True, help_text="Plain text content")
    
    # Status and flags
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unread')
    is_starred = models.BooleanField(default=False, help_text="Starred email")
    is_important = models.BooleanField(default=False, help_text="Important email")
    is_spam = models.BooleanField(default=False, help_text="Spam email")
    is_phishing = models.BooleanField(default=False, help_text="Phishing email")
    
    # Classification
    category = models.CharField(max_length=50, blank=True, help_text="Email category")
    subcategory = models.CharField(max_length=50, blank=True, help_text="Email subcategory")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    sentiment = models.CharField(max_length=20, choices=SENTIMENT_CHOICES, default='unknown')
    confidence_score = models.FloatField(default=0.0, help_text="Classification confidence score")
    
    # Attachments
    attachments = models.JSONField(default=list, help_text="Email attachments")
    attachment_count = models.PositiveIntegerField(default=0, help_text="Number of attachments")
    
    # Folder and organization
    folder = models.ForeignKey(
        EmailFolder, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='messages',
        help_text="Email folder"
    )
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    
    # Timing
    received_at = models.DateTimeField(help_text="When email was received")
    processed_at = models.DateTimeField(null=True, blank=True, help_text="When email was processed")
    read_at = models.DateTimeField(null=True, blank=True, help_text="When email was first read")
    replied_at = models.DateTimeField(null=True, blank=True, help_text="When email was replied to")
    
    # Metadata
    headers = models.JSONField(default=dict, help_text="Email headers")
    size_bytes = models.PositiveIntegerField(default=0, help_text="Email size in bytes")
    source = models.CharField(max_length=100, default='unknown', help_text="Email source")
    source_message_id = models.CharField(max_length=500, blank=True, help_text="Source message ID")
    
    # Customer and policy association
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inbox_emails',
        help_text="Associated customer"
    )
    policy = models.ForeignKey(
        'policies.Policy',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inbox_emails',
        help_text="Associated policy"
    )
    
    class Meta:
        db_table = 'email_inbox_messages'
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['from_email', 'received_at']),
            models.Index(fields=['thread_id', 'received_at']),
            models.Index(fields=['status', 'received_at']),
            models.Index(fields=['category', 'received_at']),
            models.Index(fields=['folder', 'received_at']),
            models.Index(fields=['is_starred', 'received_at']),
            models.Index(fields=['is_important', 'received_at']),
            models.Index(fields=['customer', 'received_at']),
            models.Index(fields=['policy', 'received_at']),
            models.Index(fields=['received_at']),
        ]
    
    def __str__(self):
        return f"{self.from_email} - {self.subject[:50]}"
    
    def mark_as_read(self):
        """Mark email as read"""
        if self.status == 'unread':
            self.status = 'read'
            self.read_at = timezone.now()
            self.save(update_fields=['status', 'read_at'])
    
    def mark_as_replied(self):
        """Mark email as replied"""
        self.status = 'replied'
        self.replied_at = timezone.now()
        self.save(update_fields=['status', 'replied_at'])
    
    def mark_as_forwarded(self):
        """Mark email as forwarded"""
        self.status = 'forwarded'
        self.save(update_fields=['status'])
    
    def archive(self):
        """Archive email"""
        self.status = 'archived'
        self.save(update_fields=['status'])
    
    def move_to_folder(self, folder):
        """Move email to different folder"""
        self.folder = folder
        self.save(update_fields=['folder'])
    
    def add_tag(self, tag):
        """Add tag to email"""
        if self.tags:
            tags_list = [t.strip() for t in self.tags.split(',')]
            if tag not in tags_list:
                tags_list.append(tag)
                self.tags = ', '.join(tags_list)
        else:
            self.tags = tag
        self.save(update_fields=['tags'])
    
    def remove_tag(self, tag):
        """Remove tag from email"""
        if self.tags:
            tags_list = [t.strip() for t in self.tags.split(',')]
            if tag in tags_list:
                tags_list.remove(tag)
                self.tags = ', '.join(tags_list)
                self.save(update_fields=['tags'])


class EmailConversation(BaseModel):
    """Email conversation threads"""
    
    thread_id = models.CharField(max_length=500, unique=True, help_text="Unique thread ID")
    subject = models.CharField(max_length=500, help_text="Conversation subject")
    participants = models.JSONField(default=list, help_text="Email addresses of participants")
    message_count = models.PositiveIntegerField(default=0, help_text="Number of messages in thread")
    unread_count = models.PositiveIntegerField(default=0, help_text="Number of unread messages")
    
    # Status
    is_resolved = models.BooleanField(default=False, help_text="Conversation is resolved")
    is_archived = models.BooleanField(default=False, help_text="Conversation is archived")
    is_starred = models.BooleanField(default=False, help_text="Conversation is starred")
    
    # Classification
    category = models.CharField(max_length=50, blank=True, help_text="Conversation category")
    priority = models.CharField(max_length=20, choices=EmailInboxMessage.PRIORITY_CHOICES, default='normal')
    sentiment = models.CharField(max_length=20, choices=EmailInboxMessage.SENTIMENT_CHOICES, default='unknown')
    
    # Timing
    started_at = models.DateTimeField(help_text="When conversation started")
    last_message_at = models.DateTimeField(help_text="When last message was received")
    last_activity_at = models.DateTimeField(help_text="When last activity occurred")
    
    # Customer and policy association
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_conversations',
        help_text="Associated customer"
    )
    policy = models.ForeignKey(
        'policies.Policy',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_conversations',
        help_text="Associated policy"
    )
    
    class Meta:
        db_table = 'email_conversations'
        ordering = ['-last_activity_at']
        indexes = [
            models.Index(fields=['thread_id']),
            models.Index(fields=['participants']),
            models.Index(fields=['category', 'last_activity_at']),
            models.Index(fields=['is_resolved', 'last_activity_at']),
            models.Index(fields=['customer', 'last_activity_at']),
            models.Index(fields=['policy', 'last_activity_at']),
        ]
    
    def __str__(self):
        return f"{self.subject[:50]} ({self.message_count} messages)"
    
    def update_message_count(self):
        """Update message count for this conversation"""
        self.message_count = EmailInboxMessage.objects.filter(thread_id=self.thread_id).count()
        self.unread_count = EmailInboxMessage.objects.filter(
            thread_id=self.thread_id, 
            status='unread'
        ).count()
        self.save(update_fields=['message_count', 'unread_count'])
    
    def mark_as_resolved(self):
        """Mark conversation as resolved"""
        self.is_resolved = True
        self.save(update_fields=['is_resolved'])
    
    def archive(self):
        """Archive conversation"""
        self.is_archived = True
        self.save(update_fields=['is_archived'])


class EmailFilter(BaseModel):
    """Email filters for automatic processing"""
    
    FILTER_TYPES = [
        ('incoming', 'Incoming Emails'),
        ('outgoing', 'Outgoing Emails'),
        ('both', 'Both Incoming and Outgoing'),
    ]
    
    name = models.CharField(max_length=100, help_text="Filter name")
    description = models.TextField(blank=True, help_text="Filter description")
    filter_type = models.CharField(max_length=20, choices=FILTER_TYPES, default='incoming')
    
    # Filter rules (JSON structure)
    filter_rules = models.JSONField(help_text="Filter conditions and rules")
    
    # Actions to take when filter matches
    actions = models.JSONField(help_text="Actions to perform when filter matches")
    
    # Status
    is_active = models.BooleanField(default=True, help_text="Filter is active")
    apply_to_existing = models.BooleanField(default=False, help_text="Apply to existing emails")
    
    # Statistics
    match_count = models.PositiveIntegerField(default=0, help_text="Number of emails matched")
    last_matched_at = models.DateTimeField(null=True, blank=True, help_text="When filter last matched")
    
    class Meta:
        db_table = 'email_filters'
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'filter_type']),
            models.Index(fields=['last_matched_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_filter_type_display()})"
    
    def increment_match_count(self):
        """Increment match count and update last matched time"""
        self.match_count += 1
        self.last_matched_at = timezone.now()
        self.save(update_fields=['match_count', 'last_matched_at'])


class EmailAttachment(BaseModel):
    """Email attachments"""
    
    message = models.ForeignKey(
        EmailInboxMessage,
        on_delete=models.CASCADE,
        related_name='email_attachments',
        help_text="Associated email message"
    )
    
    filename = models.CharField(max_length=255, help_text="Original filename")
    content_type = models.CharField(max_length=100, help_text="MIME content type")
    size_bytes = models.PositiveIntegerField(help_text="File size in bytes")
    
    # File storage
    file_path = models.CharField(max_length=500, help_text="File storage path")
    file_url = models.URLField(blank=True, help_text="File access URL")
    
    # Security
    is_safe = models.BooleanField(default=True, help_text="File is safe to open")
    virus_scan_status = models.CharField(max_length=20, default='pending', help_text="Virus scan status")
    virus_scan_result = models.TextField(blank=True, help_text="Virus scan result")
    
    # Metadata
    checksum = models.CharField(max_length=64, blank=True, help_text="File checksum")
    description = models.TextField(blank=True, help_text="File description")
    
    class Meta:
        db_table = 'email_attachments'
        ordering = ['filename']
        indexes = [
            models.Index(fields=['message', 'filename']),
            models.Index(fields=['content_type']),
            models.Index(fields=['is_safe', 'virus_scan_status']),
        ]
    
    def __str__(self):
        return f"{self.filename} ({self.size_bytes} bytes)"


class EmailSearchQuery(BaseModel):
    """Saved email search queries"""
    
    name = models.CharField(max_length=100, help_text="Search query name")
    description = models.TextField(blank=True, help_text="Search description")
    query_string = models.TextField(help_text="Search query string")
    search_params = models.JSONField(default=dict, help_text="Search parameters")
    
    # Statistics
    use_count = models.PositiveIntegerField(default=0, help_text="Number of times used")
    last_used_at = models.DateTimeField(null=True, blank=True, help_text="When last used")
    
    # Sharing
    is_public = models.BooleanField(default=False, help_text="Query is public")
    is_favorite = models.BooleanField(default=False, help_text="Query is favorite")
    
    class Meta:
        db_table = 'email_search_queries'
        ordering = ['-last_used_at', 'name']
        indexes = [
            models.Index(fields=['is_public', 'is_favorite']),
            models.Index(fields=['last_used_at']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.query_string[:50]}"
    
    def increment_use_count(self):
        """Increment use count and update last used time"""
        self.use_count += 1
        self.last_used_at = timezone.now()
        self.save(update_fields=['use_count', 'last_used_at'])
