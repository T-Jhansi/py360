"""
Email Operations Service Layer
"""
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Dict, List, Optional, Tuple, Any
from datetime import date
import logging

from .models import EmailMessage, EmailQueue, EmailTracking, EmailDeliveryReport, EmailAnalytics
from apps.email_provider.services import email_provider_service
from apps.email_templates.models import EmailTemplate
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

logger = logging.getLogger(__name__)


class EmailOperationsService:
    """Service for handling email operations"""
    
    def __init__(self):
        self.provider_service = email_provider_service
    
    def send_single_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str = "",
        from_email: str = "",
        from_name: str = "",
        reply_to: str = "",
        cc_emails: List[str] = None,
        bcc_emails: List[str] = None,
        template_id: Optional[int] = None,
        template_context: Dict = None,
        priority: str = "normal",
        scheduled_at: Optional[timezone.datetime] = None,
        campaign_id: str = "",
        tags: str = "",
        max_retries: int = 3,
        user=None
    ) -> Tuple[bool, str, Optional[EmailMessage]]:
        """
        Send a single email
        
        Returns:
            Tuple of (success, message, email_message)
        """
        try:
            with transaction.atomic():
                # Create email message record
                email_message = EmailMessage.objects.create(
                    to_email=to_email,
                    cc_emails=cc_emails or [],
                    bcc_emails=bcc_emails or [],
                    from_email=from_email,
                    from_name=from_name,
                    reply_to=reply_to,
                    subject=subject,
                    html_content=html_content,
                    text_content=text_content,
                    template_id=template_id,
                    template_context=template_context or {},
                    priority=priority,
                    scheduled_at=scheduled_at,
                    campaign_id=campaign_id,
                    tags=tags,
                    max_retries=max_retries,
                    created_by=user
                )
                
                # If scheduled for future, just queue it
                if scheduled_at and scheduled_at > timezone.now():
                    email_message.status = 'queued'
                    email_message.save(update_fields=['status'])
                    return True, "Email scheduled successfully", email_message
                
                # Send immediately
                return self._send_email_message(email_message)
                
        except Exception as e:
            logger.error(f"Error sending single email: {str(e)}")
            return False, f"Error sending email: {str(e)}", None
    
    def send_bulk_emails(
        self,
        recipients: List[Dict],
        template_id: int,
        from_email: str,
        from_name: str = "",
        reply_to: str = "",
        cc_emails: List[str] = None,
        bcc_emails: List[str] = None,
        priority: str = "normal",
        scheduled_at: Optional[timezone.datetime] = None,
        campaign_id: str = "",
        tags: str = "",
        max_retries: int = 3,
        user=None
    ) -> Tuple[bool, str, List[EmailMessage]]:
        """
        Send bulk emails
        
        Returns:
            Tuple of (success, message, email_messages)
        """
        try:
            # Get template
            template = EmailTemplate.objects.get(id=template_id, is_deleted=False)
            
            email_messages = []
            with transaction.atomic():
                for recipient in recipients:
                    # Render template with recipient context
                    rendered = template.render_content(recipient.get('context', {}))
                    
                    # Create email message
                    email_message = EmailMessage.objects.create(
                        to_email=recipient['email'],
                        cc_emails=cc_emails or [],
                        bcc_emails=bcc_emails or [],
                        from_email=from_email,
                        from_name=from_name,
                        reply_to=reply_to,
                        subject=rendered['subject'],
                        html_content=rendered['html_content'],
                        text_content=rendered['text_content'],
                        template=template,
                        template_context=recipient.get('context', {}),
                        priority=priority,
                        scheduled_at=scheduled_at,
                        campaign_id=campaign_id,
                        tags=tags,
                        max_retries=max_retries,
                        created_by=user
                    )
                    
                    email_messages.append(email_message)
                
                # If scheduled for future, just queue them
                if scheduled_at and scheduled_at > timezone.now():
                    EmailMessage.objects.filter(
                        id__in=[msg.id for msg in email_messages]
                    ).update(status='queued')
                    return True, f"Scheduled {len(email_messages)} emails successfully", email_messages
                
                # Send immediately
                success_count = 0
                for email_message in email_messages:
                    success, _, _ = self._send_email_message(email_message)
                    if success:
                        success_count += 1
                
                return True, f"Sent {success_count}/{len(email_messages)} emails successfully", email_messages
                
        except EmailTemplate.DoesNotExist:
            return False, "Template not found", []
        except Exception as e:
            logger.error(f"Error sending bulk emails: {str(e)}")
            return False, f"Error sending bulk emails: {str(e)}", []
    
    def _send_email_message(self, email_message: EmailMessage) -> Tuple[bool, str, EmailMessage]:
        """
        Send a single email message using the provider service
        
        Returns:
            Tuple of (success, message, email_message)
        """
        try:
            # Update status to sending
            email_message.status = 'sending'
            email_message.save(update_fields=['status'])
            
            # Send via provider service
            try:
                result = self.provider_service.send_email(
                    to_emails=[email_message.to_email],
                    subject=email_message.subject,
                    html_content=email_message.html_content,
                    text_content=email_message.text_content,
                    from_email=email_message.from_email,
                    from_name=email_message.from_name,
                    reply_to=email_message.reply_to,
                    cc_emails=email_message.cc_emails,
                    bcc_emails=email_message.bcc_emails
                )
            except Exception as e:
                # Fallback to Django's built-in email backend
                logger.warning(f"Provider service failed, using Django fallback: {str(e)}")
                result = self._send_via_django_fallback(email_message)
            
            if result['success']:
                # Mark as sent
                email_message.mark_as_sent(
                    provider_name=result.get('provider_name', 'Unknown'),
                    provider_message_id=result.get('message_id', '')
                )
                
                # Create tracking event
                EmailTracking.objects.create(
                    email=email_message,
                    event_type='sent',
                    event_data={'provider': result.get('provider_name')}
                )
                
                # Update template usage if applicable
                if email_message.template:
                    email_message.template.increment_usage()
                
                return True, "Email sent successfully", email_message
            else:
                # Mark as failed
                email_message.mark_as_failed(result.get('error', 'Unknown error'))
                return False, result.get('error', 'Failed to send email'), email_message
                
        except Exception as e:
            logger.error(f"Error sending email message {email_message.id}: {str(e)}")
            email_message.mark_as_failed(str(e))
            return False, f"Error sending email: {str(e)}", email_message
    
    def get_email_status(self, message_id: str) -> Optional[Dict]:
        """Get email status by message ID"""
        try:
            email_message = EmailMessage.objects.get(message_id=message_id)
            return {
                'message_id': email_message.message_id,
                'status': email_message.status,
                'status_display': email_message.get_status_display(),
                'sent_at': email_message.sent_at,
                'delivered_at': email_message.delivered_at,
                'opened_at': email_message.opened_at,
                'clicked_at': email_message.clicked_at,
                'open_count': email_message.open_count,
                'click_count': email_message.click_count,
                'error_message': email_message.error_message,
                'provider_used': email_message.provider_used
            }
        except EmailMessage.DoesNotExist:
            return None
    
    def get_email_tracking_data(self, message_id: str) -> Optional[Dict]:
        """Get email tracking data by message ID"""
        try:
            email_message = EmailMessage.objects.get(message_id=message_id)
            tracking_events = EmailTracking.objects.filter(email=email_message).order_by('-event_timestamp')
            
            return {
                'message_id': email_message.message_id,
                'total_events': tracking_events.count(),
                'events': list(tracking_events.values()),
                'open_tracking_url': f"/api/email-operations/track/open/{email_message.message_id}/",
                'click_tracking_base_url': f"/api/email-operations/track/click/{email_message.message_id}/"
            }
        except EmailMessage.DoesNotExist:
            return None
    
    def track_email_open(self, message_id: str, ip_address: str = None, user_agent: str = None) -> bool:
        """Track email open event"""
        try:
            email_message = EmailMessage.objects.get(message_id=message_id)
            
            # Mark as opened
            email_message.mark_as_opened()
            
            # Create tracking event
            EmailTracking.objects.create(
                email=email_message,
                event_type='opened',
                ip_address=ip_address,
                user_agent=user_agent,
                event_data={'timestamp': timezone.now().isoformat()}
            )
            
            return True
        except EmailMessage.DoesNotExist:
            return False
    
    def track_email_click(
        self, 
        message_id: str, 
        clicked_url: str, 
        link_text: str = "", 
        ip_address: str = None, 
        user_agent: str = None
    ) -> bool:
        """Track email click event"""
        try:
            email_message = EmailMessage.objects.get(message_id=message_id)
            
            # Mark as clicked
            email_message.mark_as_clicked()
            
            # Create tracking event
            EmailTracking.objects.create(
                email=email_message,
                event_type='clicked',
                clicked_url=clicked_url,
                link_text=link_text,
                ip_address=ip_address,
                user_agent=user_agent,
                event_data={'timestamp': timezone.now().isoformat()}
            )
            
            return True
        except EmailMessage.DoesNotExist:
            return False
    
    def retry_failed_emails(self, message_ids: List[str], force_retry: bool = False) -> Tuple[int, int]:
        """
        Retry failed emails
        
        Returns:
            Tuple of (successful_retries, failed_retries)
        """
        successful_retries = 0
        failed_retries = 0
        
        for message_id in message_ids:
            try:
                email_message = EmailMessage.objects.get(message_id=message_id)
                
                # Check if can retry
                if not force_retry and not email_message.can_retry():
                    failed_retries += 1
                    continue
                
                # Reset status and retry
                email_message.status = 'pending'
                email_message.error_message = ''
                email_message.save(update_fields=['status', 'error_message'])
                
                # Send again
                success, _, _ = self._send_email_message(email_message)
                if success:
                    successful_retries += 1
                else:
                    failed_retries += 1
                    
            except EmailMessage.DoesNotExist:
                failed_retries += 1
                continue
        
        return successful_retries, failed_retries
    
    def get_queue_status(self) -> Dict:
        """Get email queue status"""
        total_queued = EmailMessage.objects.filter(status='queued').count()
        total_processing = EmailMessage.objects.filter(status='sending').count()
        total_completed = EmailMessage.objects.filter(status__in=['sent', 'delivered', 'opened', 'clicked']).count()
        total_failed = EmailMessage.objects.filter(status__in=['failed', 'bounced']).count()
        
        # Calculate average processing time
        completed_emails = EmailMessage.objects.filter(
            status__in=['sent', 'delivered', 'opened', 'clicked'],
            sent_at__isnull=False,
            created_at__isnull=False
        )
        
        avg_processing_time = 0
        if completed_emails.exists():
            total_time = sum([
                (email.sent_at - email.created_at).total_seconds() 
                for email in completed_emails 
                if email.sent_at and email.created_at
            ])
            avg_processing_time = total_time / completed_emails.count()
        
        return {
            'total_queued': total_queued,
            'total_processing': total_processing,
            'total_completed': total_completed,
            'total_failed': total_failed,
            'avg_processing_time': avg_processing_time,
            'estimated_completion': None  # Could be calculated based on queue size and processing rate
        }
    
    def generate_delivery_report(self, report_date: date, provider_name: str = None) -> EmailDeliveryReport:
        """Generate delivery report for a specific date"""
        # Filter emails for the report date
        emails_query = EmailMessage.objects.filter(
            created_at__date=report_date
        )
        
        if provider_name:
            emails_query = emails_query.filter(provider_used=provider_name)
        
        emails = emails_query.all()
        
        # Calculate statistics
        total_sent = emails.count()
        total_delivered = emails.filter(status__in=['delivered', 'opened', 'clicked']).count()
        total_opened = emails.filter(status__in=['opened', 'clicked']).count()
        total_clicked = emails.filter(status='clicked').count()
        total_bounced = emails.filter(status='bounced').count()
        total_failed = emails.filter(status='failed').count()
        
        # Create or update report
        report, created = EmailDeliveryReport.objects.get_or_create(
            report_date=report_date,
            provider_name=provider_name or 'All Providers',
            defaults={
                'total_sent': total_sent,
                'total_delivered': total_delivered,
                'total_opened': total_opened,
                'total_clicked': total_clicked,
                'total_bounced': total_bounced,
                'total_failed': total_failed
            }
        )
        
        if not created:
            report.total_sent = total_sent
            report.total_delivered = total_delivered
            report.total_opened = total_opened
            report.total_clicked = total_clicked
            report.total_bounced = total_bounced
            report.total_failed = total_failed
        
        # Calculate rates
        report.calculate_rates()
        report.save()
        
        return report
    
    def get_analytics_summary(
        self, 
        period_start: timezone.datetime, 
        period_end: timezone.datetime,
        template_id: Optional[int] = None,
        campaign_id: str = ""
    ) -> Dict:
        """Get analytics summary for a period"""
        # Filter emails for the period
        emails_query = EmailMessage.objects.filter(
            created_at__gte=period_start,
            created_at__lte=period_end
        )
        
        if template_id:
            emails_query = emails_query.filter(template_id=template_id)
        
        if campaign_id:
            emails_query = emails_query.filter(campaign_id=campaign_id)
        
        emails = emails_query.all()
        
        # Calculate statistics
        total_sent = emails.count()
        total_delivered = emails.filter(status__in=['delivered', 'opened', 'clicked']).count()
        total_opened = emails.filter(status__in=['opened', 'clicked']).count()
        total_clicked = emails.filter(status='clicked').count()
        
        # Calculate rates
        delivery_rate = (total_delivered / total_sent * 100) if total_sent > 0 else 0
        open_rate = (total_opened / total_sent * 100) if total_sent > 0 else 0
        click_rate = (total_clicked / total_sent * 100) if total_sent > 0 else 0
        
        # Get top performing templates
        template_stats = {}
        for email in emails.filter(template__isnull=False):
            template_name = email.template.name
            if template_name not in template_stats:
                template_stats[template_name] = {
                    'sent': 0, 'opened': 0, 'clicked': 0
                }
            template_stats[template_name]['sent'] += 1
            if email.status in ['opened', 'clicked']:
                template_stats[template_name]['opened'] += 1
            if email.status == 'clicked':
                template_stats[template_name]['clicked'] += 1
        
        # Calculate template performance
        top_templates = []
        for template_name, stats in template_stats.items():
            open_rate = (stats['opened'] / stats['sent'] * 100) if stats['sent'] > 0 else 0
            click_rate = (stats['clicked'] / stats['sent'] * 100) if stats['sent'] > 0 else 0
            top_templates.append({
                'name': template_name,
                'sent': stats['sent'],
                'open_rate': open_rate,
                'click_rate': click_rate
            })
        
        top_templates.sort(key=lambda x: x['open_rate'], reverse=True)
        
        # Get provider performance
        provider_stats = {}
        for email in emails.filter(provider_used__isnull=False):
            provider = email.provider_used
            if provider not in provider_stats:
                provider_stats[provider] = {
                    'sent': 0, 'delivered': 0, 'failed': 0
                }
            provider_stats[provider]['sent'] += 1
            if email.status in ['delivered', 'opened', 'clicked']:
                provider_stats[provider]['delivered'] += 1
            if email.status in ['failed', 'bounced']:
                provider_stats[provider]['failed'] += 1
        
        return {
            'period_start': period_start,
            'period_end': period_end,
            'total_emails_sent': total_sent,
            'total_emails_delivered': total_delivered,
            'total_emails_opened': total_opened,
            'total_emails_clicked': total_clicked,
            'overall_delivery_rate': delivery_rate,
            'overall_open_rate': open_rate,
            'overall_click_rate': click_rate,
            'top_performing_templates': top_templates[:5],
            'provider_performance': provider_stats
        }
    
    def _send_via_django_fallback(self, email_message: EmailMessage) -> Dict[str, Any]:
        """
        Fallback method using Django's built-in email backend
        """
        try:
            # Create email message
            msg = EmailMultiAlternatives(
                subject=email_message.subject,
                body=email_message.text_content or email_message.html_content,
                from_email=email_message.from_email or settings.DEFAULT_FROM_EMAIL,
                to=[email_message.to_email],
                cc=email_message.cc_emails or [],
                bcc=email_message.bcc_emails or []
            )
            
            # Add HTML content if available
            if email_message.html_content:
                msg.attach_alternative(email_message.html_content, "text/html")
            
            # Send email
            msg.send()
            
            return {
                'success': True,
                'provider_name': 'Django SMTP Fallback',
                'message_id': f'django_{email_message.message_id}',
                'response_time': 0.1
            }
            
        except Exception as e:
            logger.error(f"Django fallback failed: {str(e)}")
            return {
                'success': False,
                'error': f"Django fallback failed: {str(e)}",
                'provider_name': 'Django SMTP Fallback'
            }


# Create service instance
email_operations_service = EmailOperationsService()
