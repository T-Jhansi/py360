# services.py

import logging
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.template import Template, Context
from .models import Campaign, CampaignRecipient
from apps.customers.models import Customer
from apps.policies.models import Policy

logger = logging.getLogger(__name__)

# Check if Celery is available
try:
    from celery import shared_task
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    def shared_task(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

class EmailCampaignService:
    """Service class for handling email campaigns"""
    
    @staticmethod
    def send_campaign_emails(campaign_id):
        """
        Send emails for a specific campaign
        """
        try:
            import traceback

            logger.info(f"Starting email sending for campaign {campaign_id}")

            campaign = Campaign.objects.get(id=campaign_id)
            logger.info(f"Found campaign: {campaign.name}")

            # Check if campaign has email channel
            if 'email' not in campaign.channels:
                logger.warning(f"Campaign {campaign_id} does not include email channel")
                return {"error": "Campaign does not include email channel"}

            # Get pending recipients
            recipients = CampaignRecipient.objects.filter(
                campaign=campaign,
                email_status='pending'
            ).select_related('customer', 'policy')

            logger.info(f"Found {recipients.count()} pending recipients")

            if not recipients.exists():
                logger.warning(f"No pending recipients found for campaign {campaign_id}")
                return {"message": "No pending recipients found for this campaign"}

            sent_count = 0
            failed_count = 0

            for recipient in recipients:
                try:
                    logger.info(f"Processing recipient {recipient.pk}: {recipient.customer.email}")

                    # Send email to recipient
                    success = EmailCampaignService._send_individual_email(recipient)

                    if success:
                        recipient.email_status = 'sent'
                        recipient.email_sent_at = timezone.now()
                        sent_count += 1
                        logger.info(f"Email sent successfully to {recipient.customer.email}")
                    else:
                        recipient.email_status = 'failed'
                        failed_count += 1
                        logger.error(f"Email failed to {recipient.customer.email}")

                    recipient.save()

                except Exception as e:
                    logger.error(f"Error sending email to recipient {recipient.pk}: {str(e)}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    recipient.email_status = 'failed'
                    recipient.save()
                    failed_count += 1

            # Update campaign statistics using the model method
            campaign.update_campaign_statistics()

            if sent_count > 0:
                campaign.status = 'completed' if failed_count == 0 else 'running'

            campaign.save()

            logger.info(f"Campaign {campaign_id} email sending completed: {sent_count} sent, {failed_count} failed")

            # Schedule delivery status update if emails were sent
            if sent_count > 0:
                EmailCampaignService._schedule_delivery_status_update(campaign.pk)

            return {
                "success": True,
                "sent_count": sent_count,
                "failed_count": failed_count,
                "message": f"Sent {sent_count} emails successfully, {failed_count} failed"
            }

        except Campaign.DoesNotExist:
            logger.error(f"Campaign {campaign_id} not found")
            return {"error": "Campaign not found"}
        except Exception as e:
            logger.error(f"Error sending campaign emails: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {"error": str(e)}
    
    @staticmethod
    def _send_individual_email(recipient):
        """
        Send email to individual recipient with tracking
        """
        try:
            from django.core.mail import EmailMultiAlternatives
            import traceback

            customer = recipient.customer
            campaign = recipient.campaign

            logger.info(f"Starting email send to {customer.email} for campaign {campaign.id}")

            # Update recipient status to queued
            recipient.email_status = 'queued'
            recipient.save()

            # Get email template content
            template_content = campaign.template.content if campaign.template else "Default email content"
            subject = campaign.template.subject if campaign.template else campaign.name

            logger.info(f"Email subject: {subject}")
            logger.info(f"Template content length: {len(template_content)}")

            # Replace template variables
            email_content = EmailCampaignService._process_template(
                template_content,
                customer,
                recipient.policy,
                campaign,
                recipient  # Pass recipient for tracking
            )

            # Add tracking pixel and wrap URLs with click tracking
            tracked_content = EmailCampaignService._add_email_tracking(email_content, recipient, campaign)

            # Create plain text version (without HTML tags)
            import re
            plain_text = re.sub(r'<[^>]+>', '', tracked_content)
            plain_text = plain_text.replace('&nbsp;', ' ').strip()

            logger.info(f"Creating email message for {customer.email}")

            # Create email message with HTML content
            msg = EmailMultiAlternatives(
                subject=subject,
                body=plain_text,  # Plain text version without HTML
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[customer.email]
            )

            # Add HTML version with tracking (this is the important part)
            msg.attach_alternative(tracked_content, "text/html")

            # Store the email content for debugging
            recipient.email_content = {
                'html': tracked_content,
                'plain': plain_text,
                'subject': subject
            }

            logger.info(f"Attempting to send email to {customer.email}")

            # Send email with detailed error handling
            try:
                msg.send(fail_silently=False)
                logger.info(f"Email sent successfully to {customer.email}")
            except Exception as send_error:
                logger.error(f"Email send failed to {customer.email}: {str(send_error)}")
                logger.error(f"Email send traceback: {traceback.format_exc()}")
                raise send_error

            # Update recipient status to sent (and assume delivered for testing)
            recipient.email_status = 'delivered'  # Changed from 'sent' to 'delivered'
            recipient.email_sent_at = timezone.now()
            recipient.save()

            # Update campaign statistics immediately
            campaign.update_campaign_statistics()

            logger.info(f"Email sent and delivered successfully to {customer.email}")
            return True

        except Exception as e:
            logger.error(f"Error sending individual email: {str(e)}")
            recipient.email_status = 'failed'
            recipient.email_error_message = str(e)
            recipient.save()
            return False
    
    @staticmethod
    def _process_template(template_content, customer, policy, campaign, recipient=None):
        """
        Process template with customer and policy data
        """
        try:
            from django.template import Template, Context

            # Create template context
            context_data = {
                'customer_name': f"{customer.first_name} {customer.last_name}",
                'customer_email': customer.email,
                'customer_phone': customer.phone,
                'company_name': 'Your Insurance Company',
                'campaign_name': campaign.name,
                'email': customer.email,
                'phone': customer.phone,
            }

            # Add customer address data
            context_data.update({
                'address': getattr(customer, 'address', ''),
                'city': getattr(customer, 'city', ''),
                'state': getattr(customer, 'state', ''),
                'postal_code': getattr(customer, 'postal_code', ''),
            })

            # Add policy data if available
            if policy:
                context_data.update({
                    'policy_number': policy.policy_number,
                    'policy_type': policy.policy_type.name if policy.policy_type else 'N/A',
                    'expiry_date': policy.end_date.strftime('%Y-%m-%d') if policy.end_date else 'N/A',
                    'start_date': policy.start_date.strftime('%Y-%m-%d') if policy.start_date else 'N/A',
                    'premium_amount': str(policy.premium_amount) if hasattr(policy, 'premium_amount') else 'N/A',
                    'policy_status': policy.status if hasattr(policy, 'status') else 'Active',
                    'renewal_link': f"http://localhost:8000/renew/{policy.policy_number}/"
                })

            # Process template using Django template engine
            template = Template(template_content)
            context = Context(context_data)
            processed_content = template.render(context)

            return processed_content

        except Exception as e:
            logger.error(f"Error processing template: {str(e)}")
            # Fallback to simple string replacement
            processed_content = template_content
            context_data = {
                'customer_name': f"{customer.first_name} {customer.last_name}",
                'customer_email': customer.email,
                'customer_phone': customer.phone,
                'company_name': 'Your Insurance Company',
                'campaign_name': campaign.name,
            }

            for key, value in context_data.items():
                processed_content = processed_content.replace(f'{{{{{key}}}}}', str(value))

            return processed_content

    @staticmethod
    def _add_email_tracking(email_content, recipient, campaign):
        """
        Add tracking pixel and wrap URLs with click tracking using secure tracking ID
        """
        try:
            import re
            from urllib.parse import quote
            from django.conf import settings

            # Ensure recipient has tracking ID
            if not recipient.tracking_id:
                recipient.save()  # This will generate tracking_id

            # Get base URL from settings or use localhost for development
            base_url = getattr(settings, 'BASE_URL', "http://localhost:8000")

            # Create tracking URLs using secure tracking ID
            tracking_pixel_url = f"{base_url}/api/campaigns/track-open/?t={recipient.tracking_id}"

            # Create a medium-sized tracking image that's more reliable than tiny pixels
            tracking_pixel = f'''
<!-- Email Open Tracking Image -->
<div style="text-align: center; margin: 20px 0; padding: 10px;">
    <img src="{tracking_pixel_url}" width="150" height="50" style="display: block; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 5px; background-color: #f8f9fa;" alt="Email Analytics" title="Email Analytics" />
    <p style="font-size: 10px; color: #888; margin: 5px 0 0 0; text-align: center;">Email Analytics & Tracking</p>
</div>
'''

            # Ensure content is HTML format
            if not ('<html>' in email_content.lower() or '<body>' in email_content.lower()):
                # Convert plain text to HTML
                html_content = email_content.replace('\n', '<br>\n')
                email_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    {html_content}
    {tracking_pixel}
</body>
</html>'''
            else:
                # Add pixel before closing body tag or at the end
                if '</body>' in email_content.lower():
                    email_content = email_content.replace('</body>', f'{tracking_pixel}\n</body>')
                elif '</html>' in email_content.lower():
                    email_content = email_content.replace('</html>', f'{tracking_pixel}\n</html>')
                else:
                    email_content += f'\n{tracking_pixel}'

            # Wrap URLs with click tracking
            url_pattern = r'href=["\']([^"\']+)["\']'

            def replace_url(match):
                original_url = match.group(1)
                # Skip tracking for certain URL types
                if (original_url.startswith('mailto:') or
                    original_url.startswith('#') or
                    original_url.startswith('tel:') or
                    'track-' in original_url or
                    tracking_pixel_url in original_url):
                    return match.group(0)

                encoded_url = quote(original_url)
                tracking_url = f"{base_url}/api/campaigns/track-click/?t={recipient.tracking_id}&url={encoded_url}"
                return f'href="{tracking_url}"'

            tracked_content = re.sub(url_pattern, replace_url, email_content)

            # Debug logging
            logger.info(f"Added tracking to email for recipient {recipient.id}, campaign {campaign.id}")
            logger.info(f"Tracking pixel URL: {tracking_pixel_url}")

            return tracked_content

        except Exception as e:
            logger.error(f"Error adding email tracking: {str(e)}")
            return email_content

    @staticmethod
    def create_campaign_recipients(campaign, target_audience_type, file_upload=None):
        """
        Create campaign recipients based on target audience
        """
        try:
            recipients_created = 0
            
            if target_audience_type == 'all_customers':
                # Get all customers
                customers = Customer.objects.all()
                
                for customer in customers:
                    # Get customer's latest policy (if any)
                    latest_policy = Policy.objects.filter(
                        customer=customer
                    ).order_by('-created_at').first()
                    
                    # Create recipient
                    recipient, created = CampaignRecipient.objects.get_or_create(
                        campaign=campaign,
                        customer=customer,
                        defaults={
                            'policy': latest_policy,
                            'email_status': 'pending'
                        }
                    )
                    
                    if created:
                        recipients_created += 1
            
            elif target_audience_type == 'expired_policies':
                # Get customers with expired policies
                expired_policies = Policy.objects.filter(
                    end_date__lt=timezone.now().date(),
                    renewal_status='pending'
                )
                
                for policy in expired_policies:
                    recipient, created = CampaignRecipient.objects.get_or_create(
                        campaign=campaign,
                        customer=policy.customer,
                        defaults={
                            'policy': policy,
                            'email_status': 'pending'
                        }
                    )
                    
                    if created:
                        recipients_created += 1
            
            elif target_audience_type == 'file_customers' and file_upload:
                # Get customers from uploaded file
                # This would need to be implemented based on your file upload logic
                pass
            
            return recipients_created
            
        except Exception as e:
            logger.error(f"Error creating campaign recipients: {str(e)}")
            return 0

    @staticmethod
    def _schedule_delivery_status_update(campaign_id):
        """
        Schedule delivery status update for sent emails
        """
        try:
            # Schedule task to run after 2 minutes (simulate email delivery time)
            update_delivery_status_task.apply_async(
                args=[campaign_id],
                countdown=120  # 2 minutes delay
            )

        except Exception as e:
            logger.error(f"Error scheduling delivery status update: {str(e)}")

    @staticmethod
    def update_delivery_status(campaign_id):
        """
        Update delivery status for sent emails (simulates real email delivery tracking)
        """
        try:
            from .models import Campaign, CampaignRecipient
            import random

            campaign = Campaign.objects.get(id=campaign_id)
            sent_recipients = CampaignRecipient.objects.filter(
                campaign=campaign,
                email_status='sent'
            )

            delivered_count = 0
            bounced_count = 0

            for recipient in sent_recipients:
                # Simulate delivery success rate (90% success, 10% bounce)
                if random.random() < 0.9:  # 90% delivery success
                    recipient.mark_delivered('email')
                    delivered_count += 1
                else:
                    recipient.email_status = 'bounced'
                    recipient.save()
                    bounced_count += 1

            # Update campaign statistics
            campaign.update_campaign_statistics()

            logger.info(f"Updated delivery status for campaign {campaign_id}: {delivered_count} delivered, {bounced_count} bounced")

            return {
                "delivered_count": delivered_count,
                "bounced_count": bounced_count
            }

        except Exception as e:
            logger.error(f"Error updating delivery status: {str(e)}")
            return {"error": str(e)}

# Celery task for async email sending
@shared_task(bind=True, max_retries=3)
def send_campaign_emails_async(self, campaign_id):
    """
    Async task to send campaign emails
    """
    try:
        result = EmailCampaignService.send_campaign_emails(campaign_id)
        return result
    except Exception as e:
        logger.error(f"Error in async email sending: {str(e)}")
        raise self.retry(countdown=60, exc=e)

# Celery task for delivery status updates
@shared_task(bind=True, max_retries=3)
def update_delivery_status_task(self, campaign_id):
    """
    Async task to update email delivery status
    """
    try:
        result = EmailCampaignService.update_delivery_status(campaign_id)
        return result
    except Exception as e:
        logger.error(f"Error updating delivery status: {str(e)}")
        raise self.retry(countdown=60, exc=e)
