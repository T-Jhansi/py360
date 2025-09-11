"""
Email Inbox Service Layer
"""
from django.utils import timezone
from django.db import transaction, models
from django.core.exceptions import ValidationError
from typing import Dict, List, Optional, Tuple, Any
from datetime import date, datetime
import logging
import re
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from .models import (
    EmailInboxMessage, EmailConversation, EmailFolder, EmailFilter,
    EmailAttachment, EmailSearchQuery
)
from apps.email_operations.services import email_operations_service

logger = logging.getLogger(__name__)


class EmailInboxService:
    """Service for handling email inbox operations"""
    
    def __init__(self):
        self.operations_service = email_operations_service
    
    def receive_email(
        self,
        message_id: str,
        from_email: str,
        from_name: str = "",
        to_emails: List[str] = None,
        cc_emails: List[str] = None,
        bcc_emails: List[str] = None,
        reply_to: str = "",
        subject: str = "",
        html_content: str = "",
        text_content: str = "",
        headers: Dict = None,
        attachments: List[Dict] = None,
        source: str = "unknown",
        source_message_id: str = ""
    ) -> Tuple[bool, str, Optional[EmailInboxMessage]]:
        """
        Receive and process an incoming email
        
        Returns:
            Tuple of (success, message, email_message)
        """
        try:
            with transaction.atomic():
                # Check if email already exists
                if EmailInboxMessage.objects.filter(message_id=message_id).exists():
                    return False, "Email already exists", None
                
                # Generate thread ID if not provided
                thread_id = self._generate_thread_id(subject, from_email, to_emails)
                
                # Get default folder
                default_folder = self._get_default_folder('inbox')
                
                # Create email message
                email_message = EmailInboxMessage.objects.create(
                    message_id=message_id,
                    thread_id=thread_id,
                    from_email=from_email,
                    from_name=from_name,
                    to_emails=to_emails or [],
                    cc_emails=cc_emails or [],
                    bcc_emails=bcc_emails or [],
                    reply_to=reply_to,
                    subject=subject,
                    html_content=html_content,
                    text_content=text_content,
                    headers=headers or {},
                    attachments=attachments or [],
                    attachment_count=len(attachments) if attachments else 0,
                    size_bytes=self._calculate_email_size(html_content, text_content, attachments),
                    source=source,
                    source_message_id=source_message_id,
                    received_at=timezone.now(),
                    processed_at=timezone.now(),
                    folder=default_folder
                )
                
                # Process attachments
                if attachments:
                    self._process_attachments(email_message, attachments)
                
                # Auto-classify email
                self._auto_classify_email(email_message)
                
                # Update conversation
                self._update_conversation(email_message)
                
                # Apply filters
                self._apply_filters(email_message)
                
                # Associate with customer/policy if possible
                self._associate_customer_policy(email_message)
                
                return True, "Email received successfully", email_message
                
        except Exception as e:
            logger.error(f"Error receiving email: {str(e)}")
            return False, f"Error receiving email: {str(e)}", None
    
    def _generate_thread_id(self, subject: str, from_email: str, to_emails: List[str]) -> str:
        """Generate thread ID for email conversation"""
        # Simple thread ID generation based on subject and participants
        participants = sorted([from_email] + (to_emails or []))
        subject_clean = re.sub(r'^(re:|fwd?:|fw:)\s*', '', subject.lower().strip())
        thread_key = f"{subject_clean}:{':'.join(participants)}"
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, thread_key))
    
    def _get_default_folder(self, folder_type: str) -> Optional[EmailFolder]:
        """Get default folder by type"""
        try:
            return EmailFolder.objects.get(folder_type=folder_type, is_system=True)
        except EmailFolder.DoesNotExist:
            return None
    
    def _calculate_email_size(self, html_content: str, text_content: str, attachments: List[Dict]) -> int:
        """Calculate total email size in bytes"""
        size = len(html_content.encode('utf-8')) + len(text_content.encode('utf-8'))
        if attachments:
            size += sum(attachment.get('size', 0) for attachment in attachments)
        return size
    
    def _process_attachments(self, email_message: EmailInboxMessage, attachments: List[Dict]):
        """Process email attachments"""
        for attachment_data in attachments:
            try:
                EmailAttachment.objects.create(
                    message=email_message,
                    filename=attachment_data.get('filename', ''),
                    content_type=attachment_data.get('content_type', 'application/octet-stream'),
                    size_bytes=attachment_data.get('size', 0),
                    file_path=attachment_data.get('file_path', ''),
                    file_url=attachment_data.get('file_url', ''),
                    checksum=attachment_data.get('checksum', ''),
                    description=attachment_data.get('description', '')
                )
            except Exception as e:
                logger.error(f"Error processing attachment: {str(e)}")
    
    def _auto_classify_email(self, email_message: EmailInboxMessage):
        """Auto-classify email based on content and sender"""
        try:
            # Simple classification based on keywords
            subject_lower = email_message.subject.lower()
            content_lower = (email_message.html_content + email_message.text_content).lower()
            
            # Policy renewal keywords
            renewal_keywords = ['renewal', 'renew', 'expire', 'expiry', 'expiring']
            if any(keyword in subject_lower or keyword in content_lower for keyword in renewal_keywords):
                email_message.category = 'policy_renewal'
                email_message.priority = 'high'
            
            # Claim keywords
            elif any(keyword in subject_lower or keyword in content_lower for keyword in ['claim', 'claims', 'accident', 'damage', 'loss']):
                email_message.category = 'claim'
                email_message.priority = 'high'
            
            # Payment keywords
            elif any(keyword in subject_lower or keyword in content_lower for keyword in ['payment', 'premium', 'bill', 'invoice', 'due']):
                email_message.category = 'payment'
                email_message.priority = 'normal'
            
            # Complaint keywords
            elif any(keyword in subject_lower or keyword in content_lower for keyword in ['complaint', 'unhappy', 'dissatisfied', 'problem', 'issue']):
                email_message.category = 'complaint'
                email_message.priority = 'high'
                email_message.sentiment = 'negative'
            
            # Inquiry keywords
            elif any(keyword in subject_lower or keyword in content_lower for keyword in ['question', 'inquiry', 'help', 'information', 'query']):
                email_message.category = 'inquiry'
                email_message.priority = 'normal'
            
            # Thank you keywords
            elif any(keyword in subject_lower or keyword in content_lower for keyword in ['thank', 'thanks', 'appreciate', 'grateful']):
                email_message.category = 'feedback'
                email_message.sentiment = 'positive'
                email_message.priority = 'low'
            
            else:
                email_message.category = 'general'
                email_message.priority = 'normal'
            
            # Set confidence score
            email_message.confidence_score = 0.8
            
            email_message.save(update_fields=['category', 'priority', 'sentiment', 'confidence_score'])
            
        except Exception as e:
            logger.error(f"Error auto-classifying email: {str(e)}")
    
    def _update_conversation(self, email_message: EmailInboxMessage):
        """Update or create conversation thread"""
        try:
            conversation, created = EmailConversation.objects.get_or_create(
                thread_id=email_message.thread_id,
                defaults={
                    'subject': email_message.subject,
                    'participants': list(set([email_message.from_email] + email_message.to_emails)),
                    'started_at': email_message.received_at,
                    'last_message_at': email_message.received_at,
                    'last_activity_at': email_message.received_at,
                    'category': email_message.category,
                    'priority': email_message.priority,
                    'sentiment': email_message.sentiment
                }
            )
            
            if not created:
                # Update existing conversation
                conversation.last_message_at = email_message.received_at
                conversation.last_activity_at = email_message.received_at
                conversation.participants = list(set(conversation.participants + [email_message.from_email] + email_message.to_emails))
                conversation.save()
            
            # Update message count
            conversation.update_message_count()
            
        except Exception as e:
            logger.error(f"Error updating conversation: {str(e)}")
    
    def _apply_filters(self, email_message: EmailInboxMessage):
        """Apply email filters to the message"""
        try:
            active_filters = EmailFilter.objects.filter(is_active=True)
            
            for email_filter in active_filters:
                if self._filter_matches(email_message, email_filter.filter_rules):
                    self._apply_filter_actions(email_message, email_filter.actions)
                    email_filter.increment_match_count()
                    
        except Exception as e:
            logger.error(f"Error applying filters: {str(e)}")
    
    def _filter_matches(self, email_message: EmailInboxMessage, filter_rules: Dict) -> bool:
        """Check if email matches filter rules"""
        try:
            # Simple filter matching logic
            for rule in filter_rules.get('rules', []):
                field = rule.get('field')
                operator = rule.get('operator')
                value = rule.get('value')
                
                if field == 'from_email':
                    if operator == 'contains' and value not in email_message.from_email:
                        return False
                    elif operator == 'equals' and email_message.from_email != value:
                        return False
                
                elif field == 'subject':
                    if operator == 'contains' and value.lower() not in email_message.subject.lower():
                        return False
                    elif operator == 'equals' and email_message.subject.lower() != value.lower():
                        return False
                
                elif field == 'category':
                    if operator == 'equals' and email_message.category != value:
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking filter match: {str(e)}")
            return False
    
    def _apply_filter_actions(self, email_message: EmailInboxMessage, actions: List[Dict]):
        """Apply filter actions to email message"""
        try:
            for action in actions:
                action_type = action.get('type')
                
                if action_type == 'move_to_folder':
                    folder_name = action.get('folder')
                    try:
                        folder = EmailFolder.objects.get(name=folder_name)
                        email_message.move_to_folder(folder)
                    except EmailFolder.DoesNotExist:
                        pass
                
                elif action_type == 'add_tag':
                    tag = action.get('tag')
                    if tag:
                        email_message.add_tag(tag)
                
                elif action_type == 'mark_important':
                    email_message.is_important = True
                    email_message.save(update_fields=['is_important'])
                
                elif action_type == 'mark_spam':
                    email_message.is_spam = True
                    email_message.save(update_fields=['is_spam'])
                
                elif action_type == 'set_priority':
                    priority = action.get('priority')
                    if priority in ['low', 'normal', 'high', 'urgent']:
                        email_message.priority = priority
                        email_message.save(update_fields=['priority'])
                        
        except Exception as e:
            logger.error(f"Error applying filter actions: {str(e)}")
    
    def _associate_customer_policy(self, email_message: EmailInboxMessage):
        """Associate email with customer and policy if possible"""
        try:
            # Try to find customer by email
            from apps.customers.models import Customer
            try:
                customer = Customer.objects.filter(
                    email=email_message.from_email
                ).first()
                if customer:
                    email_message.customer = customer
                    email_message.save(update_fields=['customer'])
                    
                    # Try to find associated policy
                    from apps.policies.models import Policy
                    policy = Policy.objects.filter(
                        customer=customer,
                        is_active=True
                    ).first()
                    if policy:
                        email_message.policy = policy
                        email_message.save(update_fields=['policy'])
                        
            except Exception as e:
                logger.error(f"Error associating customer: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error associating customer/policy: {str(e)}")
    
    def search_emails(
        self,
        query: str = "",
        folder_id: Optional[int] = None,
        status: str = "",
        category: str = "",
        priority: str = "",
        is_starred: Optional[bool] = None,
        is_important: Optional[bool] = None,
        has_attachments: Optional[bool] = None,
        from_email: str = "",
        to_email: str = "",
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        customer_id: Optional[int] = None,
        policy_id: Optional[int] = None,
        sort_by: str = "received_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Search emails with filters and pagination"""
        try:
            queryset = EmailInboxMessage.objects.filter(is_deleted=False)
            
            # Apply filters
            if query:
                queryset = queryset.filter(
                    models.Q(subject__icontains=query) |
                    models.Q(html_content__icontains=query) |
                    models.Q(text_content__icontains=query) |
                    models.Q(from_name__icontains=query)
                )
            
            if folder_id:
                queryset = queryset.filter(folder_id=folder_id)
            
            if status:
                queryset = queryset.filter(status=status)
            
            if category:
                queryset = queryset.filter(category=category)
            
            if priority:
                queryset = queryset.filter(priority=priority)
            
            if is_starred is not None:
                queryset = queryset.filter(is_starred=is_starred)
            
            if is_important is not None:
                queryset = queryset.filter(is_important=is_important)
            
            if has_attachments is not None:
                if has_attachments:
                    queryset = queryset.filter(attachment_count__gt=0)
                else:
                    queryset = queryset.filter(attachment_count=0)
            
            if from_email:
                queryset = queryset.filter(from_email__icontains=from_email)
            
            if to_email:
                queryset = queryset.filter(to_emails__contains=[to_email])
            
            if date_from:
                queryset = queryset.filter(received_at__date__gte=date_from)
            
            if date_to:
                queryset = queryset.filter(received_at__date__lte=date_to)
            
            if customer_id:
                queryset = queryset.filter(customer_id=customer_id)
            
            if policy_id:
                queryset = queryset.filter(policy_id=policy_id)
            
            # Apply sorting
            if sort_order == 'desc':
                sort_field = f'-{sort_by}'
            else:
                sort_field = sort_by
            
            queryset = queryset.order_by(sort_field)
            
            # Apply pagination
            total_count = queryset.count()
            start = (page - 1) * page_size
            end = start + page_size
            emails = queryset[start:end]
            
            return {
                'emails': list(emails.values()),
                'total_count': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size
            }
            
        except Exception as e:
            logger.error(f"Error searching emails: {str(e)}")
            return {'emails': [], 'total_count': 0, 'page': 1, 'page_size': page_size, 'total_pages': 0}
    
    def reply_to_email(
        self,
        original_message_id: int,
        subject: str,
        html_content: str,
        text_content: str = "",
        cc_emails: List[str] = None,
        bcc_emails: List[str] = None,
        attachments: List = None,
        user=None
    ) -> Tuple[bool, str, Optional[Dict]]:
        """Reply to an email"""
        try:
            original_message = EmailInboxMessage.objects.get(id=original_message_id)
            
            # Prepare reply content
            reply_subject = f"Re: {original_message.subject}" if not subject.startswith('Re:') else subject
            
            # Send reply using email operations service
            success, message, sent_email = self.operations_service.send_single_email(
                to_email=original_message.from_email,
                subject=reply_subject,
                html_content=html_content,
                text_content=text_content,
                from_email="noreply@company.com",  # Should be configurable
                from_name="Insurance Company",
                reply_to="support@company.com",
                cc_emails=cc_emails or [],
                bcc_emails=bcc_emails or [],
                priority='normal',
                campaign_id=f"reply_{original_message.message_id}",
                tags="reply",
                user=user
            )
            
            if success:
                # Mark original message as replied
                original_message.mark_as_replied()
                
                return True, "Reply sent successfully", {
                    'original_message_id': original_message.id,
                    'sent_email_id': sent_email.id if sent_email else None
                }
            else:
                return False, f"Failed to send reply: {message}", None
                
        except EmailInboxMessage.DoesNotExist:
            return False, "Original message not found", None
        except Exception as e:
            logger.error(f"Error replying to email: {str(e)}")
            return False, f"Error replying to email: {str(e)}", None
    
    def forward_email(
        self,
        original_message_id: int,
        to_emails: List[str],
        cc_emails: List[str] = None,
        bcc_emails: List[str] = None,
        subject: str = "",
        message: str = "",
        user=None
    ) -> Tuple[bool, str, Optional[Dict]]:
        """Forward an email"""
        try:
            original_message = EmailInboxMessage.objects.get(id=original_message_id)
            
            # Prepare forward content
            forward_subject = f"Fwd: {original_message.subject}" if not subject else subject
            
            # Create forward content
            forward_html = f"""
            <p>{message}</p>
            <hr>
            <p><strong>From:</strong> {original_message.from_name} &lt;{original_message.from_email}&gt;</p>
            <p><strong>Date:</strong> {original_message.received_at}</p>
            <p><strong>Subject:</strong> {original_message.subject}</p>
            <hr>
            {original_message.html_content}
            """
            
            forward_text = f"""
            {message}
            
            ---
            From: {original_message.from_name} <{original_message.from_email}>
            Date: {original_message.received_at}
            Subject: {original_message.subject}
            
            {original_message.text_content}
            """
            
            # Send forward using email operations service
            success, message, sent_email = self.operations_service.send_single_email(
                to_email=to_emails[0] if to_emails else "",
                subject=forward_subject,
                html_content=forward_html,
                text_content=forward_text,
                from_email="noreply@company.com",  # Should be configurable
                from_name="Insurance Company",
                reply_to="support@company.com",
                cc_emails=cc_emails or [],
                bcc_emails=bcc_emails or [],
                priority='normal',
                campaign_id=f"forward_{original_message.message_id}",
                tags="forward",
                user=user
            )
            
            if success:
                # Mark original message as forwarded
                original_message.mark_as_forwarded()
                
                return True, "Email forwarded successfully", {
                    'original_message_id': original_message.id,
                    'sent_email_id': sent_email.id if sent_email else None
                }
            else:
                return False, f"Failed to forward email: {message}", None
                
        except EmailInboxMessage.DoesNotExist:
            return False, "Original message not found", None
        except Exception as e:
            logger.error(f"Error forwarding email: {str(e)}")
            return False, f"Error forwarding email: {str(e)}", None
    
    def get_email_statistics(self) -> Dict[str, Any]:
        """Get email statistics"""
        try:
            now = timezone.now()
            today = now.date()
            week_ago = now - timezone.timedelta(days=7)
            month_ago = now - timezone.timedelta(days=30)
            
            # Basic counts
            total_emails = EmailInboxMessage.objects.filter(is_deleted=False).count()
            unread_emails = EmailInboxMessage.objects.filter(status='unread', is_deleted=False).count()
            starred_emails = EmailInboxMessage.objects.filter(is_starred=True, is_deleted=False).count()
            important_emails = EmailInboxMessage.objects.filter(is_important=True, is_deleted=False).count()
            spam_emails = EmailInboxMessage.objects.filter(is_spam=True, is_deleted=False).count()
            
            # Time-based counts
            emails_today = EmailInboxMessage.objects.filter(
                received_at__date=today, is_deleted=False
            ).count()
            emails_this_week = EmailInboxMessage.objects.filter(
                received_at__gte=week_ago, is_deleted=False
            ).count()
            emails_this_month = EmailInboxMessage.objects.filter(
                received_at__gte=month_ago, is_deleted=False
            ).count()
            
            # Category statistics
            category_stats = {}
            for category, count in EmailInboxMessage.objects.filter(
                is_deleted=False, category__isnull=False
            ).values('category').annotate(count=models.Count('id')).values_list('category', 'count'):
                category_stats[category] = count
            
            # Priority statistics
            priority_stats = {}
            for priority, count in EmailInboxMessage.objects.filter(
                is_deleted=False
            ).values('priority').annotate(count=models.Count('id')).values_list('priority', 'count'):
                priority_stats[priority] = count
            
            # Sentiment statistics
            sentiment_stats = {}
            for sentiment, count in EmailInboxMessage.objects.filter(
                is_deleted=False, sentiment__isnull=False
            ).values('sentiment').annotate(count=models.Count('id')).values_list('sentiment', 'count'):
                sentiment_stats[sentiment] = count
            
            # Folder statistics
            folder_stats = {}
            for folder_name, count in EmailInboxMessage.objects.filter(
                is_deleted=False, folder__isnull=False
            ).values('folder__name').annotate(count=models.Count('id')).values_list('folder__name', 'count'):
                folder_stats[folder_name] = count
            
            return {
                'total_emails': total_emails,
                'unread_emails': unread_emails,
                'starred_emails': starred_emails,
                'important_emails': important_emails,
                'spam_emails': spam_emails,
                'emails_today': emails_today,
                'emails_this_week': emails_this_week,
                'emails_this_month': emails_this_month,
                'category_stats': category_stats,
                'priority_stats': priority_stats,
                'sentiment_stats': sentiment_stats,
                'folder_stats': folder_stats
            }
            
        except Exception as e:
            logger.error(f"Error getting email statistics: {str(e)}")
            return {}


# Create service instance
email_inbox_service = EmailInboxService()
