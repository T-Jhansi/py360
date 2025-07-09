from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import BaseModel, TimestampedModel
from apps.customers.models import Customer
from apps.policies.models import Policy
import uuid
import json

User = get_user_model()

class EmailAccount(BaseModel):
    """Email accounts for IMAP/SMTP integration"""
    ACCOUNT_TYPE_CHOICES = [
        ('imap', 'IMAP'),
        ('pop3', 'POP3'),
        ('exchange', 'Exchange'),
        ('gmail', 'Gmail API'),
        ('outlook', 'Outlook API'),
    ]
    
    name = models.CharField(max_length=200)
    email_address = models.EmailField(unique=True)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES, default='imap')
    
    # Server settings
    incoming_server = models.CharField(max_length=200)
    incoming_port = models.PositiveIntegerField(default=993)
    incoming_security = models.CharField(max_length=10, choices=[
        ('ssl', 'SSL'),
        ('tls', 'TLS'),
        ('none', 'None'),
    ], default='ssl')
    
    outgoing_server = models.CharField(max_length=200)
    outgoing_port = models.PositiveIntegerField(default=587)
    outgoing_security = models.CharField(max_length=10, choices=[
        ('ssl', 'SSL'),
        ('tls', 'TLS'),
        ('none', 'None'),
    ], default='tls')
    
    # Authentication
    username = models.CharField(max_length=200)
    password = models.CharField(max_length=500)  # Encrypted
    
    # API credentials (for Gmail/Outlook API)
    api_credentials = models.JSONField(default=dict, blank=True)
    
    # Settings
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    auto_sync = models.BooleanField(default=True)
    sync_interval = models.PositiveIntegerField(default=300, help_text="Sync interval in seconds")
    
    # Sync status
    last_sync_at = models.DateTimeField(null=True, blank=True)
    sync_status = models.CharField(max_length=20, choices=[
        ('connected', 'Connected'),
        ('error', 'Error'),
        ('syncing', 'Syncing'),
        ('disabled', 'Disabled'),
    ], default='connected')
    sync_error = models.TextField(blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'email_accounts'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.email_address})"

class EmailFolder(BaseModel):
    """Email folders/labels"""
    account = models.ForeignKey(EmailAccount, on_delete=models.CASCADE, related_name='folders')
    name = models.CharField(max_length=200)
    display_name = models.CharField(max_length=200)
    folder_type = models.CharField(max_length=20, choices=[
        ('inbox', 'Inbox'),
        ('sent', 'Sent'),
        ('drafts', 'Drafts'),
        ('trash', 'Trash'),
        ('spam', 'Spam'),
        ('custom', 'Custom'),
    ], default='custom')
    
    # Folder properties
    is_selectable = models.BooleanField(default=True)
    message_count = models.PositiveIntegerField(default=0)
    unread_count = models.PositiveIntegerField(default=0)
    
    # Sync settings
    auto_sync = models.BooleanField(default=True)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'email_folders'
        unique_together = ['account', 'name']
        ordering = ['account', 'name']
    
    def __str__(self):
        return f"{self.account.name} - {self.display_name}"

class EmailThread(BaseModel):
    """Email conversation threads"""
    subject = models.CharField(max_length=500)
    participants = models.JSONField(default=list)  # List of email addresses
    
    # Thread properties
    message_count = models.PositiveIntegerField(default=0)
    unread_count = models.PositiveIntegerField(default=0)
    is_important = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    
    # Customer association
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='email_threads')
    policy = models.ForeignKey(Policy, on_delete=models.SET_NULL, null=True, blank=True, related_name='email_threads')
    
    # Thread dates
    first_message_date = models.DateTimeField()
    last_message_date = models.DateTimeField()
    
    # Assignment
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_email_threads')
    
    # Labels/Tags
    labels = models.JSONField(default=list, blank=True)
    
    class Meta:
        db_table = 'email_threads'
        ordering = ['-last_message_date']
        indexes = [
            models.Index(fields=['customer', 'last_message_date']),
            models.Index(fields=['assigned_to', 'is_archived']),
        ]
    
    def __str__(self):
        return f"Thread: {self.subject[:50]}"

class Email(BaseModel):
    """Individual email messages"""
    MESSAGE_TYPE_CHOICES = [
        ('received', 'Received'),
        ('sent', 'Sent'),
        ('draft', 'Draft'),
    ]
    
    # Basic email fields
    message_id = models.CharField(max_length=500, unique=True)
    thread = models.ForeignKey(EmailThread, on_delete=models.CASCADE, related_name='emails')
    account = models.ForeignKey(EmailAccount, on_delete=models.CASCADE, related_name='emails')
    folder = models.ForeignKey(EmailFolder, on_delete=models.CASCADE, related_name='emails')
    
    # Email headers
    subject = models.CharField(max_length=500)
    from_email = models.EmailField()
    from_name = models.CharField(max_length=200, blank=True)
    to_emails = models.JSONField(default=list)
    cc_emails = models.JSONField(default=list, blank=True)
    bcc_emails = models.JSONField(default=list, blank=True)
    reply_to = models.EmailField(blank=True)
    
    # Content
    html_content = models.TextField(blank=True)
    text_content = models.TextField(blank=True)
    
    # Email properties
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES)
    is_read = models.BooleanField(default=False)
    is_important = models.BooleanField(default=False)
    is_flagged = models.BooleanField(default=False)
    is_spam = models.BooleanField(default=False)
    
    # Dates
    sent_date = models.DateTimeField()
    received_date = models.DateTimeField(null=True, blank=True)
    read_date = models.DateTimeField(null=True, blank=True)
    
    # Size and attachments
    size = models.PositiveIntegerField(default=0)
    has_attachments = models.BooleanField(default=False)
    attachment_count = models.PositiveIntegerField(default=0)
    
    # Customer/Policy association
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='emails')
    policy = models.ForeignKey(Policy, on_delete=models.SET_NULL, null=True, blank=True, related_name='emails')
    
    # Processing
    is_processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    processing_notes = models.TextField(blank=True)
    
    # Classification
    email_category = models.CharField(max_length=50, choices=[
        ('inquiry', 'General Inquiry'),
        ('renewal', 'Renewal Request'),
        ('claim', 'Claim Related'),
        ('complaint', 'Complaint'),
        ('payment', 'Payment Related'),
        ('document', 'Document Submission'),
        ('feedback', 'Feedback'),
        ('other', 'Other'),
    ], blank=True)
    
    # AI/ML fields
    sentiment_score = models.FloatField(null=True, blank=True, help_text="Sentiment analysis score")
    intent = models.CharField(max_length=100, blank=True, help_text="Detected customer intent")
    priority_score = models.PositiveIntegerField(default=0, help_text="AI-calculated priority (0-100)")
    
    # Response tracking
    requires_response = models.BooleanField(default=False)
    response_due_date = models.DateTimeField(null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='email_responses')
    
    class Meta:
        db_table = 'emails'
        ordering = ['-sent_date']
        indexes = [
            models.Index(fields=['account', 'folder', 'sent_date']),
            models.Index(fields=['customer', 'sent_date']),
            models.Index(fields=['message_type', 'is_read']),
            models.Index(fields=['requires_response', 'response_due_date']),
        ]
    
    def __str__(self):
        return f"{self.subject[:50]} - {self.from_email}"

class EmailAttachment(BaseModel):
    """Email attachments"""
    email = models.ForeignKey(Email, on_delete=models.CASCADE, related_name='attachments')
    filename = models.CharField(max_length=500)
    content_type = models.CharField(max_length=100)
    size = models.PositiveIntegerField()
    
    # File storage
    file = models.FileField(upload_to='email_attachments/', null=True, blank=True)
    file_path = models.CharField(max_length=1000, blank=True)
    
    # Attachment properties
    is_inline = models.BooleanField(default=False)
    content_id = models.CharField(max_length=200, blank=True)
    
    # Processing
    is_scanned = models.BooleanField(default=False)
    scan_result = models.CharField(max_length=20, choices=[
        ('clean', 'Clean'),
        ('suspicious', 'Suspicious'),
        ('malicious', 'Malicious'),
        ('error', 'Scan Error'),
    ], blank=True)
    
    class Meta:
        db_table = 'email_attachments'
        ordering = ['filename']
    
    def __str__(self):
        return f"{self.filename} ({self.email.subject[:30]})"

class EmailTemplate(BaseModel):
    """Email templates for responses"""
    TEMPLATE_TYPE_CHOICES = [
        ('response', 'Response Template'),
        ('auto_reply', 'Auto Reply'),
        ('signature', 'Email Signature'),
        ('campaign', 'Campaign Template'),
    ]
    
    name = models.CharField(max_length=200)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPE_CHOICES)
    category = models.CharField(max_length=50, choices=[
        ('renewal', 'Renewal'),
        ('claim', 'Claim'),
        ('general', 'General Inquiry'),
        ('complaint', 'Complaint'),
        ('payment', 'Payment'),
        ('welcome', 'Welcome'),
        ('follow_up', 'Follow Up'),
    ])
    
    # Template content
    subject = models.CharField(max_length=200)
    html_content = models.TextField()
    text_content = models.TextField(blank=True)
    
    # Template variables
    variables = models.JSONField(default=list, help_text="List of template variables")
    
    # Usage tracking
    usage_count = models.PositiveIntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'email_templates'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.template_type})"

class EmailRule(BaseModel):
    """Email processing rules"""
    RULE_TYPE_CHOICES = [
        ('filter', 'Filter Rule'),
        ('auto_assign', 'Auto Assignment'),
        ('auto_reply', 'Auto Reply'),
        ('forward', 'Forward Rule'),
        ('classification', 'Classification Rule'),
    ]
    
    name = models.CharField(max_length=200)
    rule_type = models.CharField(max_length=20, choices=RULE_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    priority = models.PositiveIntegerField(default=0)
    
    # Rule conditions
    conditions = models.JSONField(default=dict)
    # Example: {
    #   "from_contains": ["@example.com"],
    #   "subject_contains": ["renewal", "policy"],
    #   "body_contains": ["urgent"],
    #   "has_attachments": true
    # }
    
    # Rule actions
    actions = models.JSONField(default=dict)
    # Example: {
    #   "assign_to_user": 123,
    #   "set_category": "renewal",
    #   "set_priority": 5,
    #   "send_auto_reply": "template_id",
    #   "forward_to": "manager@company.com"
    # }
    
    # Statistics
    matches_count = models.PositiveIntegerField(default=0)
    last_matched = models.DateTimeField(null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'email_rules'
        ordering = ['-priority', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.rule_type})"

class EmailSignature(BaseModel):
    """Email signatures for users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_signatures')
    name = models.CharField(max_length=200)
    html_signature = models.TextField()
    text_signature = models.TextField(blank=True)
    
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'email_signatures'
        ordering = ['user', 'name']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.name}"

class EmailActivity(BaseModel):
    """Email activity log"""
    ACTION_CHOICES = [
        ('received', 'Email Received'),
        ('sent', 'Email Sent'),
        ('read', 'Email Read'),
        ('replied', 'Email Replied'),
        ('forwarded', 'Email Forwarded'),
        ('archived', 'Email Archived'),
        ('deleted', 'Email Deleted'),
        ('assigned', 'Email Assigned'),
        ('processed', 'Email Processed'),
    ]
    
    email = models.ForeignKey(Email, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField(blank=True)
    
    # User who performed the action
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Additional data
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'email_activities'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'action']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.action} - {self.email.subject[:30]}"

class EmailSyncLog(BaseModel):
    """Email synchronization logs"""
    account = models.ForeignKey(EmailAccount, on_delete=models.CASCADE, related_name='sync_logs')
    sync_type = models.CharField(max_length=20, choices=[
        ('full', 'Full Sync'),
        ('incremental', 'Incremental Sync'),
        ('manual', 'Manual Sync'),
    ])
    
    # Sync results
    status = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('partial', 'Partial Success'),
        ('failed', 'Failed'),
    ])
    
    # Statistics
    emails_processed = models.PositiveIntegerField(default=0)
    emails_added = models.PositiveIntegerField(default=0)
    emails_updated = models.PositiveIntegerField(default=0)
    emails_deleted = models.PositiveIntegerField(default=0)
    
    # Timing
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    
    # Error details
    error_message = models.TextField(blank=True)
    error_details = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'email_sync_logs'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.account.name} - {self.sync_type} - {self.status}" 