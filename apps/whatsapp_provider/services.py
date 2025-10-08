import logging
import time
import requests
import json
from typing import List, Dict, Any, Optional, Tuple
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from cryptography.fernet import Fernet
from .models import (
    WhatsAppBusinessAccount,
    WhatsAppPhoneNumber,
    WhatsAppMessage,
    WhatsAppMessageTemplate,
    WhatsAppWebhookEvent,
    WhatsAppFlow,
    WhatsAppAccountHealthLog,
    WhatsAppAccountUsageLog,
)

logger = logging.getLogger(__name__)


class WhatsAppAPIError(Exception):
    """Custom exception for WhatsApp API errors"""
    pass


class WhatsAppService:
    """Service for managing WhatsApp Business API operations"""
    
    def __init__(self):
        self.encryption_key = getattr(settings, 'WHATSAPP_ENCRYPTION_KEY', None)
        self._fernet = None
        if self.encryption_key:
            try:
                self._fernet = Fernet(self.encryption_key.encode())
            except Exception as e:
                logger.error(f"Failed to initialize WhatsApp encryption: {e}")
        
        # WhatsApp Cloud API base URL
        self.api_base_url = "https://graph.facebook.com/v18.0"
    
    def _encrypt_credential(self, value: str) -> str:
        """Encrypt a credential value"""
        if not self._fernet or not value:
            return value
        try:
            return self._fernet.encrypt(value.encode()).decode()
        except Exception as e:
            logger.error(f"Failed to encrypt WhatsApp credential: {e}")
            return value
    
    def _decrypt_credential(self, value: str) -> str:
        """Decrypt a credential value"""
        if not self._fernet or not value:
            return value
        try:
            return self._fernet.decrypt(value.encode()).decode()
        except Exception as e:
            logger.error(f"Failed to decrypt WhatsApp credential: {e}")
            return value
    
    def _make_api_request(self, url: str, method: str = 'GET', data: Dict = None, 
                         access_token: str = None) -> Dict[str, Any]:
        """Make API request to WhatsApp Cloud API"""
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                raise WhatsAppAPIError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"WhatsApp API request failed: {e}")
            raise WhatsAppAPIError(f"API request failed: {str(e)}")
    
    def get_active_waba_accounts(self) -> List[WhatsAppBusinessAccount]:
        """Get all active WhatsApp Business accounts"""
        return WhatsAppBusinessAccount.objects.filter(
            is_active=True,
            is_deleted=False,
            status='verified'
        ).order_by('priority', 'name')
    
    def get_available_waba_account(self) -> Optional[WhatsAppBusinessAccount]:
        """Get the first available WABA account that can send messages"""
        accounts = self.get_active_waba_accounts()
        
        for account in accounts:
            if account.can_send_message():
                return account
        
        return None
    
    def create_message_template(self, waba_account: WhatsAppBusinessAccount, 
                              template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a message template in WhatsApp Business API"""
        access_token = self._decrypt_credential(waba_account.access_token)
        
        url = f"{self.api_base_url}/{waba_account.waba_id}/message_templates"
        
        data = {
            'name': template_data['name'],
            'category': template_data['category'],
            'language': template_data['language'],
            'components': template_data.get('components', [])
        }
        
        try:
            response = self._make_api_request(url, 'POST', data, access_token)
            
            # Update template in database
            template = WhatsAppMessageTemplate.objects.create(
                waba_account=waba_account,
                name=template_data['name'],
                category=template_data['category'],
                language=template_data['language'],
                header_text=template_data.get('header_text', ''),
                body_text=template_data.get('body_text', ''),
                footer_text=template_data.get('footer_text', ''),
                components=template_data.get('components', []),
                meta_template_id=response.get('id'),
                status='pending'
            )
            
            logger.info(f"Created template {template.name} for WABA {waba_account.name}")
            return response
            
        except WhatsAppAPIError as e:
            logger.error(f"Failed to create template: {e}")
            raise
    
    def send_text_message(self, waba_account: WhatsAppBusinessAccount,
                         phone_number: WhatsAppPhoneNumber, to_phone: str,
                         text_content: str, customer=None, campaign=None) -> Dict[str, Any]:
        """Send a text message via WhatsApp Business API"""
        access_token = self._decrypt_credential(waba_account.access_token)
        
        url = f"{self.api_base_url}/{phone_number.phone_number_id}/messages"
        
        data = {
            'messaging_product': 'whatsapp',
            'to': to_phone,
            'type': 'text',
            'text': {
                'body': text_content
            }
        }
        
        try:
            response = self._make_api_request(url, 'POST', data, access_token)
            
            # Create message record
            message = WhatsAppMessage.objects.create(
                waba_account=waba_account,
                phone_number=phone_number,
                message_id=response['messages'][0]['id'],
                direction='outbound',
                message_type='text',
                to_phone_number=to_phone,
                from_phone_number=phone_number.phone_number,
                content={'text': text_content},
                status='sent',
                sent_at=timezone.now(),
                customer=customer,
                campaign=campaign
            )
            
            # Update usage counters
            self._update_usage_counters(waba_account, phone_number)
            
            logger.info(f"Sent text message to {to_phone} via WABA {waba_account.name}")
            return response
            
        except WhatsAppAPIError as e:
            logger.error(f"Failed to send text message: {e}")
            raise
    
    def send_template_message(self, waba_account: WhatsAppBusinessAccount,
                            phone_number: WhatsAppPhoneNumber, to_phone: str,
                            template: WhatsAppMessageTemplate, 
                            template_params: List[str] = None,
                            customer=None, campaign=None) -> Dict[str, Any]:
        """Send a template message via WhatsApp Business API"""
        access_token = self._decrypt_credential(waba_account.access_token)
        
        url = f"{self.api_base_url}/{phone_number.phone_number_id}/messages"
        
        data = {
            'messaging_product': 'whatsapp',
            'to': to_phone,
            'type': 'template',
            'template': {
                'name': template.name,
                'language': {
                    'code': template.language
                }
            }
        }
        
        # Add template parameters if provided
        if template_params:
            data['template']['components'] = [
                {
                    'type': 'body',
                    'parameters': [{'type': 'text', 'text': param} for param in template_params]
                }
            ]
        
        try:
            response = self._make_api_request(url, 'POST', data, access_token)
            
            # Create message record
            message = WhatsAppMessage.objects.create(
                waba_account=waba_account,
                phone_number=phone_number,
                message_id=response['messages'][0]['id'],
                direction='outbound',
                message_type='template',
                to_phone_number=to_phone,
                from_phone_number=phone_number.phone_number,
                content={'template': template.name, 'params': template_params or []},
                template=template,
                status='sent',
                sent_at=timezone.now(),
                customer=customer,
                campaign=campaign
            )
            
            # Update usage counters
            self._update_usage_counters(waba_account, phone_number)
            
            # Update template usage
            template.usage_count += 1
            template.last_used = timezone.now()
            template.save(update_fields=['usage_count', 'last_used'])
            
            logger.info(f"Sent template message {template.name} to {to_phone} via WABA {waba_account.name}")
            return response
            
        except WhatsAppAPIError as e:
            logger.error(f"Failed to send template message: {e}")
            raise
    
    def send_interactive_message(self, waba_account: WhatsAppBusinessAccount,
                               phone_number: WhatsAppPhoneNumber, to_phone: str,
                               flow: WhatsAppFlow, flow_token: str = None,
                               customer=None, campaign=None) -> Dict[str, Any]:
        """Send an interactive message (WhatsApp Flow) via WhatsApp Business API"""
        access_token = self._decrypt_credential(waba_account.access_token)
        
        url = f"{self.api_base_url}/{phone_number.phone_number_id}/messages"
        
        data = {
            'messaging_product': 'whatsapp',
            'to': to_phone,
            'type': 'interactive',
            'interactive': {
                'type': 'flow',
                'body': {
                    'text': flow.description or 'Please complete this form:'
                },
                'action': {
                    'name': 'flow',
                    'parameters': {
                        'flow_message_version': '3',
                        'flow_token': flow_token or f"flow_token_{int(time.time())}",
                        'flow_id': flow.id,
                        'flow_cta': 'Complete Form',
                        'flow_action_payload': {
                            'screen': 'SCREEN_NAME',
                            'data': {}
                        }
                    }
                }
            }
        }
        
        try:
            response = self._make_api_request(url, 'POST', data, access_token)
            
            # Create message record
            message = WhatsAppMessage.objects.create(
                waba_account=waba_account,
                phone_number=phone_number,
                message_id=response['messages'][0]['id'],
                direction='outbound',
                message_type='interactive',
                to_phone_number=to_phone,
                from_phone_number=phone_number.phone_number,
                content={'flow_id': flow.id, 'flow_token': flow_token},
                status='sent',
                sent_at=timezone.now(),
                customer=customer,
                campaign=campaign
            )
            
            # Update usage counters
            self._update_usage_counters(waba_account, phone_number)
            
            # Update flow usage
            flow.usage_count += 1
            flow.last_used = timezone.now()
            flow.save(update_fields=['usage_count', 'last_used'])
            
            logger.info(f"Sent interactive message {flow.name} to {to_phone} via WABA {waba_account.name}")
            return response
            
        except WhatsAppAPIError as e:
            logger.error(f"Failed to send interactive message: {e}")
            raise
    
    def process_webhook_event(self, event_data: Dict[str, Any]) -> WhatsAppWebhookEvent:
        """Process incoming webhook event from WhatsApp Business API"""
        try:
            # Determine event type
            event_type = self._determine_event_type(event_data)
            
            # Find associated WABA account
            waba_account = self._find_waba_account(event_data)
            
            # Create webhook event record
            webhook_event = WhatsAppWebhookEvent.objects.create(
                waba_account=waba_account,
                event_type=event_type,
                raw_data=event_data
            )
            
            # Process based on event type
            if event_type == 'message':
                self._process_incoming_message(webhook_event, event_data)
            elif event_type == 'message_status':
                self._process_message_status_update(webhook_event, event_data)
            elif event_type == 'account_update':
                self._process_account_update(webhook_event, event_data)
            elif event_type == 'template_status':
                self._process_template_status_update(webhook_event, event_data)
            
            webhook_event.processed = True
            webhook_event.processed_at = timezone.now()
            webhook_event.save(update_fields=['processed', 'processed_at'])
            
            logger.info(f"Processed webhook event {event_type} for WABA {waba_account.name if waba_account else 'Unknown'}")
            return webhook_event
            
        except Exception as e:
            logger.error(f"Failed to process webhook event: {e}")
            if 'webhook_event' in locals():
                webhook_event.processing_error = str(e)
                webhook_event.save(update_fields=['processing_error'])
            raise
    
    def _determine_event_type(self, event_data: Dict[str, Any]) -> str:
        """Determine the type of webhook event"""
        if 'messages' in event_data:
            return 'message'
        elif 'statuses' in event_data:
            return 'message_status'
        elif 'account_update' in event_data:
            return 'account_update'
        elif 'message_template_status_update' in event_data:
            return 'template_status'
        else:
            return 'unknown'
    
    def _find_waba_account(self, event_data: Dict[str, Any]) -> Optional[WhatsAppBusinessAccount]:
        """Find WABA account from webhook event data"""
        # Try to find by phone number ID
        if 'messages' in event_data:
            for message in event_data['messages']:
                phone_number_id = message.get('from')
                if phone_number_id:
                    try:
                        phone_number = WhatsAppPhoneNumber.objects.get(
                            phone_number_id=phone_number_id,
                            is_active=True
                        )
                        return phone_number.waba_account
                    except WhatsAppPhoneNumber.DoesNotExist:
                        continue
        
        # Try to find by WABA ID in metadata
        metadata = event_data.get('metadata', {})
        waba_id = metadata.get('waba_id')
        if waba_id:
            try:
                return WhatsAppBusinessAccount.objects.get(
                    waba_id=waba_id,
                    is_active=True
                )
            except WhatsAppBusinessAccount.DoesNotExist:
                pass
        
        return None
    
    def _process_incoming_message(self, webhook_event: WhatsAppWebhookEvent, 
                                event_data: Dict[str, Any]):
        """Process incoming message from customer"""
        for message_data in event_data.get('messages', []):
            try:
                # Find phone number
                phone_number_id = message_data.get('from')
                phone_number = WhatsAppPhoneNumber.objects.get(
                    phone_number_id=phone_number_id,
                    is_active=True
                )
                
                # Create incoming message record
                WhatsAppMessage.objects.create(
                    waba_account=phone_number.waba_account,
                    phone_number=phone_number,
                    message_id=message_data['id'],
                    direction='inbound',
                    message_type=message_data.get('type', 'text'),
                    to_phone_number=phone_number.phone_number,
                    from_phone_number=message_data['from'],
                    content=message_data,
                    status='delivered'
                )
                
                logger.info(f"Processed incoming message from {message_data['from']}")
                
            except WhatsAppPhoneNumber.DoesNotExist:
                logger.warning(f"Phone number {phone_number_id} not found for incoming message")
            except Exception as e:
                logger.error(f"Failed to process incoming message: {e}")
    
    def _process_message_status_update(self, webhook_event: WhatsAppWebhookEvent,
                                     event_data: Dict[str, Any]):
        """Process message status update (delivered, read, failed)"""
        for status_data in event_data.get('statuses', []):
            try:
                message_id = status_data['id']
                status = status_data['status']
                
                # Update message status
                message = WhatsAppMessage.objects.get(message_id=message_id)
                message.status = status
                
                # Update timestamps based on status
                now = timezone.now()
                if status == 'delivered':
                    message.delivered_at = now
                elif status == 'read':
                    message.read_at = now
                elif status == 'failed':
                    message.error_code = status_data.get('errors', [{}])[0].get('code')
                    message.error_message = status_data.get('errors', [{}])[0].get('title')
                
                message.save()
                
                logger.info(f"Updated message {message_id} status to {status}")
                
            except WhatsAppMessage.DoesNotExist:
                logger.warning(f"Message {message_id} not found for status update")
            except Exception as e:
                logger.error(f"Failed to process status update: {e}")
    
    def _process_account_update(self, webhook_event: WhatsAppWebhookEvent,
                              event_data: Dict[str, Any]):
        """Process account update events"""
        account_data = event_data.get('account_update', {})
        waba_id = account_data.get('waba_id')
        
        if waba_id:
            try:
                waba_account = WhatsAppBusinessAccount.objects.get(waba_id=waba_id)
                # Update account status or other fields as needed
                logger.info(f"Processed account update for WABA {waba_account.name}")
            except WhatsAppBusinessAccount.DoesNotExist:
                logger.warning(f"WABA account {waba_id} not found for update")
    
    def _process_template_status_update(self, webhook_event: WhatsAppWebhookEvent,
                                      event_data: Dict[str, Any]):
        """Process template status update events"""
        template_data = event_data.get('message_template_status_update', {})
        template_id = template_data.get('message_template_id')
        status = template_data.get('status')
        
        if template_id:
            try:
                template = WhatsAppMessageTemplate.objects.get(meta_template_id=template_id)
                template.status = 'approved' if status == 'APPROVED' else 'rejected'
                if status == 'REJECTED':
                    template.rejection_reason = template_data.get('reason', 'Unknown reason')
                template.save()
                
                logger.info(f"Updated template {template.name} status to {status}")
                
            except WhatsAppMessageTemplate.DoesNotExist:
                logger.warning(f"Template {template_id} not found for status update")
    
    def _update_usage_counters(self, waba_account: WhatsAppBusinessAccount,
                             phone_number: WhatsAppPhoneNumber):
        """Update usage counters for WABA account and phone number"""
        now = timezone.now()
        today = now.date()
        
        # Update WABA account counters
        waba_account.messages_sent_today += 1
        waba_account.messages_sent_this_month += 1
        
        # Reset daily counter if needed
        if waba_account.last_reset_daily != today:
            waba_account.messages_sent_today = 1
            waba_account.last_reset_daily = today
        
        # Reset monthly counter if needed
        if waba_account.last_reset_monthly.month != today.month:
            waba_account.messages_sent_this_month = 1
            waba_account.last_reset_monthly = today
        
        waba_account.save(update_fields=[
            'messages_sent_today', 'messages_sent_this_month',
            'last_reset_daily', 'last_reset_monthly'
        ])
        
        # Update phone number counters
        phone_number.messages_sent_today += 1
        phone_number.messages_sent_this_month += 1
        phone_number.last_message_sent = now
        phone_number.save(update_fields=[
            'messages_sent_today', 'messages_sent_this_month', 'last_message_sent'
        ])
        
        # Update daily usage log
        usage_log, created = WhatsAppAccountUsageLog.objects.get_or_create(
            waba_account=waba_account,
            date=today,
            defaults={'messages_sent': 1}
        )
        if not created:
            usage_log.messages_sent += 1
            usage_log.save(update_fields=['messages_sent'])
    
    def health_check_waba_account(self, waba_account: WhatsAppBusinessAccount) -> Dict[str, Any]:
        """Perform health check on WABA account"""
        try:
            access_token = self._decrypt_credential(waba_account.access_token)
            url = f"{self.api_base_url}/{waba_account.waba_id}"
            
            response = self._make_api_request(url, 'GET', access_token=access_token)
            
            health_status = 'healthy'
            check_details = {
                'api_response': response,
                'checked_at': timezone.now().isoformat()
            }
            
            # Update account health
            waba_account.last_health_check = timezone.now()
            waba_account.health_status = health_status
            waba_account.save(update_fields=['last_health_check', 'health_status'])
            
            # Create health log
            WhatsAppAccountHealthLog.objects.create(
                waba_account=waba_account,
                health_status=health_status,
                check_details=check_details
            )
            
            logger.info(f"Health check passed for WABA {waba_account.name}")
            return {'status': health_status, 'details': check_details}
            
        except Exception as e:
            health_status = 'unhealthy'
            error_message = str(e)
            
            # Update account health
            waba_account.last_health_check = timezone.now()
            waba_account.health_status = health_status
            waba_account.save(update_fields=['last_health_check', 'health_status'])
            
            # Create health log
            WhatsAppAccountHealthLog.objects.create(
                waba_account=waba_account,
                health_status=health_status,
                check_details={'error': error_message},
                error_message=error_message
            )
            
            logger.error(f"Health check failed for WABA {waba_account.name}: {e}")
            return {'status': health_status, 'error': error_message}
    
    def get_waba_account_analytics(self, waba_account: WhatsAppBusinessAccount,
                                 start_date=None, end_date=None) -> Dict[str, Any]:
        """Get analytics for WABA account"""
        if not start_date:
            start_date = timezone.now().date() - timezone.timedelta(days=30)
        if not end_date:
            end_date = timezone.now().date()
        
        # Get message statistics
        messages = WhatsAppMessage.objects.filter(
            waba_account=waba_account,
            created_at__date__range=[start_date, end_date]
        )
        
        total_messages = messages.count()
        sent_messages = messages.filter(direction='outbound').count()
        received_messages = messages.filter(direction='inbound').count()
        
        # Get delivery statistics
        delivered_messages = messages.filter(status='delivered').count()
        read_messages = messages.filter(status='read').count()
        failed_messages = messages.filter(status='failed').count()
        
        # Get template usage
        template_usage = {}
        for template in waba_account.message_templates.filter(status='approved'):
            usage_count = messages.filter(template=template).count()
            if usage_count > 0:
                template_usage[template.name] = usage_count
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'messages': {
                'total': total_messages,
                'sent': sent_messages,
                'received': received_messages,
                'delivered': delivered_messages,
                'read': read_messages,
                'failed': failed_messages
            },
            'delivery_rate': (delivered_messages / sent_messages * 100) if sent_messages > 0 else 0,
            'read_rate': (read_messages / delivered_messages * 100) if delivered_messages > 0 else 0,
            'template_usage': template_usage
        }
