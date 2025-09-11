"""
Email Provider Service Layer
Unified service for managing multiple email providers with failover support
"""
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache

from .models import EmailProviderConfig, EmailProviderHealthLog, EmailProviderUsageLog
from .utils import (
    decrypt_credentials, cache_provider_credentials, get_cached_provider_credentials,
    clear_provider_cache, format_provider_error
)

logger = logging.getLogger(__name__)


class EmailProviderService:
    """Unified email provider service with failover support"""
    
    def __init__(self):
        self._providers = None
        self.health_check_interval = getattr(settings, 'EMAIL_PROVIDER_HEALTH_CHECK_INTERVAL', 300)  # 5 minutes
    
    @property
    def providers(self) -> List[EmailProviderConfig]:
        """Lazy load providers"""
        if self._providers is None:
            self._providers = self._load_providers()
        return self._providers
    
    def _load_providers(self) -> List[EmailProviderConfig]:
        """Load active providers ordered by priority"""
        try:
            return list(EmailProviderConfig.objects.filter(
                is_active=True
            ).order_by('priority', 'name')) 
        except Exception as e:
            logger.warning(f"Failed to load providers: {str(e)}")
            return []
    
    def refresh_providers(self):
        """Refresh the providers cache"""
        self._providers = None
    
    def _get_provider_credentials(self, provider: EmailProviderConfig) -> Dict[str, Any]:
        """Get provider credentials (cached or decrypted)"""
        # Try cache first
        cached_credentials = get_cached_provider_credentials(provider.id)
        if cached_credentials:
            return cached_credentials
        
        # Decrypt and cache
        credentials = decrypt_credentials(provider)
        cache_provider_credentials(provider, credentials)
        return credentials
    
    def _update_provider_usage(self, provider: EmailProviderConfig, success: bool, response_time: float):
        """Update provider usage statistics"""
        try:
            provider.total_emails_sent += 1
            if success:
                provider.emails_sent_today += 1
                provider.emails_sent_this_month += 1
            else:
                provider.total_emails_failed += 1
            
            # Update average response time
            total_requests = provider.total_emails_sent + provider.total_emails_failed
            if total_requests > 0:
                provider.average_response_time = (
                    (provider.average_response_time * (total_requests - 1) + response_time) / total_requests
                )
            
            provider.save(update_fields=[
                'total_emails_sent', 'emails_sent_today', 'emails_sent_this_month',
                'total_emails_failed', 'average_response_time'
            ])
            
            # Log usage
            today = timezone.now().date()
            usage_log, created = EmailProviderUsageLog.objects.get_or_create(
                provider=provider,
                date=today,
                defaults={'emails_sent': 0, 'emails_failed': 0, 'total_response_time': 0.0}
            )
            
            if success:
                usage_log.emails_sent += 1
            else:
                usage_log.emails_failed += 1
            
            usage_log.total_response_time += response_time
            usage_log.save()
            
        except Exception as e:
            logger.error(f"Failed to update provider usage: {str(e)}")
    
    def _log_health_check(self, provider: EmailProviderConfig, status: str, response_time: float, error_message: str = ''):
        """Log health check result"""
        try:
            EmailProviderHealthLog.objects.create(
                provider=provider,
                status=status,
                response_time=response_time,
                error_message=error_message,
                test_type='connection'
            )
        except Exception as e:
            logger.error(f"Failed to log health check: {str(e)}")
    
    def _check_provider_health(self, provider: EmailProviderConfig) -> Tuple[bool, float, str]:
        """
        Check provider health
        
        Returns:
            Tuple of (is_healthy, response_time, error_message)
        """
        start_time = time.time()
        
        try:
            credentials = self._get_provider_credentials(provider)
            
            if provider.provider_type == 'sendgrid':
                return self._check_sendgrid_health(provider, credentials)
            elif provider.provider_type == 'aws_ses':
                return self._check_aws_ses_health(provider, credentials)
            elif provider.provider_type == 'smtp':
                return self._check_smtp_health(provider, credentials)
            else:
                return False, 0.0, f"Unsupported provider type: {provider.provider_type}"
                
        except Exception as e:
            response_time = time.time() - start_time
            error_message = format_provider_error(e, provider.name)
            logger.error(error_message)
            return False, response_time, error_message
    
    def _check_sendgrid_health(self, provider: EmailProviderConfig, credentials: Dict[str, Any]) -> Tuple[bool, float, str]:
        """Check SendGrid provider health"""
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail
            
            sg = sendgrid.SendGridAPIClient(api_key=credentials.get('api_key', ''))
            
            # Test API connection
            response = sg.client.user.get()
            
            if response.status_code == 200:
                return True, 0.1, ""
            else:
                return False, 0.1, f"SendGrid API error: {response.status_code}"
                
        except ImportError:
            return False, 0.0, "SendGrid library not installed"
        except Exception as e:
            return False, 0.1, str(e)
    
    def _check_aws_ses_health(self, provider: EmailProviderConfig, credentials: Dict[str, Any]) -> Tuple[bool, float, str]:
        """Check AWS SES provider health"""
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            ses_client = boto3.client(
                'ses',
                aws_access_key_id=credentials.get('access_key_id', ''),
                aws_secret_access_key=credentials.get('secret_access_key', ''),
                region_name=credentials.get('region', 'us-east-1')
            )
            
            # Test SES connection
            response = ses_client.get_send_quota()
            
            if 'Max24HourSend' in response:
                return True, 0.2, ""
            else:
                return False, 0.2, "AWS SES connection failed"
                
        except ImportError:
            return False, 0.0, "boto3 library not installed"
        except ClientError as e:
            return False, 0.2, f"AWS SES error: {str(e)}"
        except Exception as e:
            return False, 0.2, str(e)
    
    def _check_smtp_health(self, provider: EmailProviderConfig, credentials: Dict[str, Any]) -> Tuple[bool, float, str]:
        """Check SMTP provider health"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            
            smtp_host = credentials.get('smtp_host', '')
            smtp_port = credentials.get('smtp_port', 587)
            smtp_username = credentials.get('smtp_username', '')
            smtp_password = credentials.get('smtp_password', '')
            use_tls = credentials.get('smtp_use_tls', True)
            use_ssl = credentials.get('smtp_use_ssl', False)
            
            if use_ssl:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port)
                if use_tls:
                    server.starttls()
            
            server.login(smtp_username, smtp_password)
            server.quit()
            
            return True, 0.3, ""
            
        except Exception as e:
            return False, 0.3, str(e)
    
    def health_check_all_providers(self) -> Dict[str, Any]:
        """Perform health check on all active providers"""
        results = {}
        
        for provider in self.providers:
            is_healthy, response_time, error_message = self._check_provider_health(provider)
            
            # Update provider health status
            if is_healthy:
                provider.update_health_status('healthy')
            else:
                provider.update_health_status('unhealthy', error_message)
            
            # Log health check
            self._log_health_check(provider, 'healthy' if is_healthy else 'unhealthy', response_time, error_message)
            
            results[provider.name] = {
                'healthy': is_healthy,
                'response_time': response_time,
                'error_message': error_message,
                'status': provider.health_status
            }
        
        return results
    
    def get_available_provider(self) -> Optional[EmailProviderConfig]:
        """
        Get the best available provider based on health and limits
        
        Returns:
            Available provider or None
        """
        for provider in self.providers:
            can_send, reason = provider.can_send_email()
            if can_send:
                return provider
            else:
                logger.warning(f"Provider {provider.name} unavailable: {reason}")
        
        return None
    
    def send_email(self, to_emails: List[str], subject: str, html_content: str = '', 
                   text_content: str = '', from_email: str = None, from_name: str = None,
                   reply_to: str = None, cc_emails: List[str] = None, 
                   bcc_emails: List[str] = None, attachments: List[Tuple[str, str, str]] = None) -> Dict[str, Any]:
        """
        Send email using the best available provider with failover
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text email content
            from_email: From email address (uses provider default if not provided)
            from_name: From name (uses provider default if not provided)
            reply_to: Reply-to email address
            cc_emails: CC email addresses
            bcc_emails: BCC email addresses
            attachments: List of (filename, content, mimetype) tuples
        
        Returns:
            Dictionary with send result
        """
        start_time = time.time()
        
        # Try each provider in priority order
        for provider in self.providers:
            try:
                can_send, reason = provider.can_send_email()
                if not can_send:
                    logger.warning(f"Skipping provider {provider.name}: {reason}")
                    continue
                
                result = self._send_with_provider(
                    provider, to_emails, subject, html_content, text_content,
                    from_email, from_name, reply_to, cc_emails, bcc_emails, attachments
                )
                
                if result['success']:
                    response_time = time.time() - start_time
                    self._update_provider_usage(provider, True, response_time)
                    provider.update_health_status('healthy')
                    
                    return {
                        'success': True,
                        'provider': provider.name,
                        'message_id': result.get('message_id', ''),
                        'response_time': response_time
                    }
                else:
                    logger.warning(f"Provider {provider.name} failed: {result['error']}")
                    provider.update_health_status('unhealthy', result['error'])
                    
            except Exception as e:
                error_message = format_provider_error(e, provider.name)
                logger.error(error_message)
                provider.update_health_status('unhealthy', error_message)
                continue
        
        # All providers failed
        response_time = time.time() - start_time
        return {
            'success': False,
            'error': 'All email providers failed',
            'response_time': response_time
        }
    
    def _send_with_provider(self, provider: EmailProviderConfig, to_emails: List[str], 
                           subject: str, html_content: str = '', text_content: str = '',
                           from_email: str = None, from_name: str = None, reply_to: str = None,
                           cc_emails: List[str] = None, bcc_emails: List[str] = None,
                           attachments: List[Tuple[str, str, str]] = None) -> Dict[str, Any]:
        """Send email with specific provider"""
        try:
            credentials = self._get_provider_credentials(provider)
            
            # Use provider defaults if not provided
            if not from_email:
                from_email = credentials.get('from_email', '')
            if not from_name:
                from_name = credentials.get('from_name', '')
            if not reply_to:
                reply_to = credentials.get('reply_to', '')
            
            if provider.provider_type == 'sendgrid':
                return self._send_with_sendgrid(provider, credentials, to_emails, subject, 
                                              html_content, text_content, from_email, from_name, 
                                              reply_to, cc_emails, bcc_emails, attachments)
            elif provider.provider_type == 'aws_ses':
                return self._send_with_aws_ses(provider, credentials, to_emails, subject,
                                             html_content, text_content, from_email, from_name,
                                             reply_to, cc_emails, bcc_emails, attachments)
            elif provider.provider_type == 'smtp':
                return self._send_with_smtp(provider, credentials, to_emails, subject,
                                          html_content, text_content, from_email, from_name,
                                          reply_to, cc_emails, bcc_emails, attachments)
            else:
                return {'success': False, 'error': f'Unsupported provider type: {provider.provider_type}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_with_sendgrid(self, provider: EmailProviderConfig, credentials: Dict[str, Any],
                           to_emails: List[str], subject: str, html_content: str = '', 
                           text_content: str = '', from_email: str = '', from_name: str = '',
                           reply_to: str = '', cc_emails: List[str] = None, 
                           bcc_emails: List[str] = None, attachments: List[Tuple[str, str, str]] = None) -> Dict[str, Any]:
        """Send email using SendGrid"""
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
            
            sg = sendgrid.SendGridAPIClient(api_key=credentials.get('api_key', ''))
            
            # Create email
            mail = Mail(
                from_email=(from_email, from_name) if from_name else from_email,
                to_emails=to_emails,
                subject=subject,
                html_content=html_content,
                plain_text_content=text_content
            )
            
            if reply_to:
                mail.reply_to = reply_to
            
            if cc_emails:
                mail.cc = cc_emails
            
            if bcc_emails:
                mail.bcc = bcc_emails
            
            # Add attachments
            if attachments:
                for filename, content, mimetype in attachments:
                    attachment = Attachment(
                        FileContent(content),
                        FileName(filename),
                        FileType(mimetype),
                        Disposition('attachment')
                    )
                    mail.add_attachment(attachment)
            
            # Send email
            response = sg.send(mail)
            
            if response.status_code in [200, 201, 202]:
                return {
                    'success': True,
                    'message_id': response.headers.get('X-Message-Id', ''),
                    'status_code': response.status_code
                }
            else:
                return {
                    'success': False,
                    'error': f'SendGrid API error: {response.status_code}',
                    'status_code': response.status_code
                }
                
        except ImportError:
            return {'success': False, 'error': 'SendGrid library not installed'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_with_aws_ses(self, provider: EmailProviderConfig, credentials: Dict[str, Any],
                          to_emails: List[str], subject: str, html_content: str = '',
                          text_content: str = '', from_email: str = '', from_name: str = '',
                          reply_to: str = '', cc_emails: List[str] = None,
                          bcc_emails: List[str] = None, attachments: List[Tuple[str, str, str]] = None) -> Dict[str, Any]:
        """Send email using AWS SES"""
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            ses_client = boto3.client(
                'ses',
                aws_access_key_id=credentials.get('access_key_id', ''),
                aws_secret_access_key=credentials.get('secret_access_key', ''),
                region_name=credentials.get('region', 'us-east-1')
            )
            
            # Prepare message
            message = {
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {}
            }
            
            if html_content:
                message['Body']['Html'] = {'Data': html_content, 'Charset': 'UTF-8'}
            
            if text_content:
                message['Body']['Text'] = {'Data': text_content, 'Charset': 'UTF-8'}
            
            # Send email
            response = ses_client.send_email(
                Source=from_email,
                Destination={
                    'ToAddresses': to_emails,
                    'CcAddresses': cc_emails or [],
                    'BccAddresses': bcc_emails or []
                },
                Message=message,
                ReplyToAddresses=[reply_to] if reply_to else []
            )
            
            return {
                'success': True,
                'message_id': response.get('MessageId', ''),
                'response_metadata': response.get('ResponseMetadata', {})
            }
            
        except ImportError:
            return {'success': False, 'error': 'boto3 library not installed'}
        except ClientError as e:
            return {'success': False, 'error': f'AWS SES error: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_with_smtp(self, provider: EmailProviderConfig, credentials: Dict[str, Any],
                       to_emails: List[str], subject: str, html_content: str = '',
                       text_content: str = '', from_email: str = '', from_name: str = '',
                       reply_to: str = '', cc_emails: List[str] = None,
                       bcc_emails: List[str] = None, attachments: List[Tuple[str, str, str]] = None) -> Dict[str, Any]:
        """Send email using SMTP"""
        try:
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            from email.mime.base import MIMEBase
            from email import encoders
            
            smtp_host = credentials.get('smtp_host', '')
            smtp_port = credentials.get('smtp_port', 587)
            smtp_username = credentials.get('smtp_username', '')
            smtp_password = credentials.get('smtp_password', '')
            use_tls = credentials.get('smtp_use_tls', True)
            use_ssl = credentials.get('smtp_use_ssl', False)
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{from_name} <{from_email}>" if from_name else from_email
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            if reply_to:
                msg['Reply-To'] = reply_to
            
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
            
            # Add content
            if text_content:
                msg.attach(MIMEText(text_content, 'plain'))
            
            if html_content:
                msg.attach(MIMEText(html_content, 'html'))
            
            # Add attachments
            if attachments:
                for filename, content, mimetype in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(content)
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename= {filename}')
                    msg.attach(part)
            
            # Send email
            if use_ssl:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port)
                if use_tls:
                    server.starttls()
            
            server.login(smtp_username, smtp_password)
            
            all_recipients = to_emails + (cc_emails or []) + (bcc_emails or [])
            text = msg.as_string()
            server.sendmail(from_email, all_recipients, text)
            server.quit()
            
            return {
                'success': True,
                'message_id': f"smtp_{int(time.time())}",
                'provider': 'smtp'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_provider(self, provider: EmailProviderConfig, test_email: str = None) -> Dict[str, Any]:
        """
        Test email provider by sending a test email
        
        Args:
            provider: Provider to test
            test_email: Email address to send test to (uses provider from_email if not provided)
        
        Returns:
            Test result dictionary
        """
        if not test_email:
            credentials = self._get_provider_credentials(provider)
            test_email = credentials.get('from_email', '')
        
        if not test_email:
            return {
                'success': False,
                'error': 'No test email address provided'
            }
        
        # Send test email
        result = self.send_email(
            to_emails=[test_email],
            subject='Email Provider Test',
            html_content='<p>This is a test email to verify provider configuration.</p>',
            text_content='This is a test email to verify provider configuration.'
        )
        
        return result
    
    def get_provider_statistics(self) -> Dict[str, Any]:
        """Get statistics for all providers"""
        stats = {}
        
        for provider in self.providers:
            stats[provider.name] = {
                'provider_type': provider.provider_type,
                'is_active': provider.is_active,
                'is_default': provider.is_default,
                'health_status': provider.health_status,
                'priority': provider.priority,
                'daily_limit': provider.daily_limit,
                'monthly_limit': provider.monthly_limit,
                'emails_sent_today': provider.emails_sent_today,
                'emails_sent_this_month': provider.emails_sent_this_month,
                'total_emails_sent': provider.total_emails_sent,
                'total_emails_failed': provider.total_emails_failed,
                'average_response_time': provider.average_response_time,
                'consecutive_failures': provider.consecutive_failures,
                'last_health_check': provider.last_health_check
            }
        
        return stats


# Global service instance
email_provider_service = EmailProviderService()
