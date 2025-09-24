from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import RegexValidator
from apps.core.models import BaseModel
from decimal import Decimal

User = get_user_model()

# Import the existing RenewalCase model to use as our Case model
from apps.renewals.models import RenewalCase


# Use the existing RenewalCase model as our Case model
# This ensures we work with actual business data instead of dummy data
Case = RenewalCase

# Add properties to RenewalCase to make it compatible with our case history system
def get_case_id(self):
    """Get case ID in the format expected by case history"""
    return self.case_number

def get_title(self):
    """Get case title from customer and policy info"""
    if self.customer and self.policy:
        return f"Renewal for {self.customer.full_name} - {self.policy.policy_number}"
    elif self.customer:
        return f"Renewal for {self.customer.full_name}"
    else:
        return f"Renewal Case {self.case_number}"

def get_description(self):
    """Get case description from notes"""
    return self.notes or f"Policy renewal case for {self.customer.full_name if self.customer else 'Unknown Customer'}"

def get_handling_agent(self):
    """Get handling agent (assigned_to field)"""
    return self.assigned_to

def get_started_at(self):
    """Get started date (created_at field)"""
    return self.created_at

def get_processing_days(self):
    """Calculate processing days"""
    if self.created_at:
        from django.utils import timezone
        now = timezone.now()
        if self.created_at.tzinfo is None:
            # If created_at is naive, make it timezone-aware
            from django.utils import timezone
            created_at = timezone.make_aware(self.created_at)
        else:
            created_at = self.created_at
        delta = now - created_at
        return delta.days
    return 0

def get_closed_at(self):
    """Get closed date - check if status indicates closure"""
    if self.status in ['completed', 'renewed', 'cancelled', 'expired']:
        return self.updated_at
    return None

def get_is_closed(self):
    """Check if case is closed"""
    return self.status in ['completed', 'renewed', 'cancelled', 'expired']

def get_is_active(self):
    """Check if case is active"""
    return self.status not in ['completed', 'renewed', 'cancelled', 'expired']

def close_case(self, user=None):
    """Close the case"""
    self.status = 'completed'
    if user:
        self.updated_by = user
    self.save(update_fields=['status', 'updated_by', 'updated_at'])

# Add these properties to the RenewalCase model
RenewalCase.case_id = property(get_case_id)
RenewalCase.title = property(get_title)
RenewalCase.description = property(get_description)
RenewalCase.handling_agent = property(get_handling_agent)
RenewalCase.started_at = property(get_started_at)
RenewalCase.processing_days = property(get_processing_days)
RenewalCase.closed_at = property(get_closed_at)
RenewalCase.is_closed = property(get_is_closed)
RenewalCase.is_active = property(get_is_active)
RenewalCase.close_case = close_case


class CaseHistory(BaseModel):
    ACTION_CHOICES = [
        ('case_created', 'Case Created'),
        ('case_updated', 'Case Updated'),
        ('case_closed', 'Case Closed'),
        ('case_cancelled', 'Case Cancelled'),
        ('status_changed', 'Status Changed'),
        ('agent_assigned', 'Agent Assigned'),
        ('agent_unassigned', 'Agent Unassigned'),
        ('validation', 'Validation'),
        ('assignment', 'Assignment'),
        ('comment_added', 'Comment Added'),
        ('comment_updated', 'Comment Updated'),
        ('comment_deleted', 'Comment Deleted'),
        ('document_uploaded', 'Document Uploaded'),
        ('document_removed', 'Document Removed'),
        ('communication_sent', 'Communication Sent'),
        ('follow_up_scheduled', 'Follow-up Scheduled'),
        ('escalation', 'Escalation'),
        ('other', 'Other'),
    ]
    
    case = models.ForeignKey(
        RenewalCase,
        on_delete=models.CASCADE,
        related_name='case_history',
        help_text="Case this history entry belongs to"
    )
    
    action = models.CharField(
        max_length=30,
        choices=ACTION_CHOICES,
        db_index=True,
        help_text="Type of action performed"
    )
    
    description = models.TextField(
        help_text="Detailed description of the action"
    )
    
    # Additional context
    old_value = models.TextField(
        blank=True,
        help_text="Previous value (for updates)"
    )
    new_value = models.TextField(
        blank=True,
        help_text="New value (for updates)"
    )
    
    # Related objects
    related_comment = models.ForeignKey(
        'CaseComment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='history_entries',
        help_text="Related comment if this history entry is about a comment"
    )
    
    # Additional metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata for this history entry"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['case', 'action']),
            models.Index(fields=['case', 'created_at']),
            models.Index(fields=['action', 'created_at']),
            models.Index(fields=['created_by']),
        ]
        verbose_name = 'Case History'
        verbose_name_plural = 'Case Histories'
    
    def __str__(self):
        return f"{self.case.case_id} - {self.get_action_display()} ({self.created_at})"


class CaseComment(BaseModel):
    COMMENT_TYPE_CHOICES = [
        ('general', 'General'),
        ('internal', 'Internal Note'),
        ('customer_communication', 'Customer Communication'),
        ('follow_up', 'Follow-up'),
        ('escalation', 'Escalation'),
        ('resolution', 'Resolution'),
        ('other', 'Other'),
    ]
    
    case = models.ForeignKey(
        RenewalCase,
        on_delete=models.CASCADE,
        related_name='case_comments',
        help_text="Case this comment belongs to"
    )
    
    comment = models.TextField(
        help_text="Comment content"
    )
    
    comment_type = models.CharField(
        max_length=30,
        choices=COMMENT_TYPE_CHOICES,
        default='general',
        db_index=True,
        help_text="Type of comment"
    )
    
    is_internal = models.BooleanField(
        default=False,
        help_text="Whether this is an internal comment (not visible to customer)"
    )
    
    is_important = models.BooleanField(
        default=False,
        help_text="Whether this is an important comment"
    )
    
    # Related information
    related_comment = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies',
        help_text="Parent comment if this is a reply"
    )
    
    # Additional metadata
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Comment tags"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional comment metadata"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['case', 'comment_type']),
            models.Index(fields=['case', 'created_at']),
            models.Index(fields=['is_internal', 'is_important']),
            models.Index(fields=['related_comment']),
        ]
        verbose_name = 'Case Comment'
        verbose_name_plural = 'Case Comments'
    
    def __str__(self):
        return f"{self.case.case_id} - Comment by {self.created_by} ({self.created_at})"
    
    @property
    def is_reply(self):
        """Check if this comment is a reply to another comment"""
        return self.related_comment is not None
    
    def get_replies(self):
        """Get all replies to this comment"""
        return self.replies.filter(is_deleted=False).order_by('created_at')
