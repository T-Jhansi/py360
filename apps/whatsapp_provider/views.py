from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Sum
from django.contrib.auth import get_user_model

from .models import (
    WhatsAppBusinessAccount,
    WhatsAppPhoneNumber,
    WhatsAppMessageTemplate,
    WhatsAppMessage,
    WhatsAppWebhookEvent,
    WhatsAppFlow,
    WhatsAppAccountHealthLog,
    WhatsAppAccountUsageLog,
)
from .serializers import (
    WhatsAppBusinessAccountSerializer,
    WhatsAppBusinessAccountCreateSerializer,
    WhatsAppAccountSetupSerializer,
    WhatsAppPhoneNumberSerializer,
    WhatsAppMessageTemplateSerializer,
    WhatsAppMessageSerializer,
    WhatsAppMessageCreateSerializer,
    WhatsAppMessageSendSerializer,
    WhatsAppWebhookEventSerializer,
    WhatsAppFlowSerializer,
    WhatsAppAccountHealthLogSerializer,
    WhatsAppAccountUsageLogSerializer,
)
from .services import WhatsAppService, WhatsAppAPIError

User = get_user_model()


class WhatsAppBusinessAccountViewSet(viewsets.ModelViewSet):
    """ViewSet for managing WhatsApp Business Accounts"""
    
    queryset = WhatsAppBusinessAccount.objects.filter(is_deleted=False)
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return WhatsAppBusinessAccountCreateSerializer
        elif self.action == 'setup':
            return WhatsAppAccountSetupSerializer
        return WhatsAppBusinessAccountSerializer
    
    def get_queryset(self):
        """Filter accounts based on user permissions"""
        queryset = super().get_queryset()
        
        # If user is not admin, filter by created_by
        if not self.request.user.is_staff:
            queryset = queryset.filter(created_by=self.request.user)
        
        return queryset.select_related('created_by', 'updated_by').prefetch_related(
            'phone_numbers', 'message_templates'
        )
    
    def perform_create(self, serializer):
        """Create a new WhatsApp Business Account"""
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        """Update WhatsApp Business Account"""
        serializer.save(updated_by=self.request.user)
    
    @action(detail=False, methods=['post'], url_path='setup')
    def setup(self, request):
        """Complete 6-step WhatsApp account setup"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                waba_account = serializer.save()
                response_serializer = WhatsAppBusinessAccountSerializer(waba_account)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response(
                    {'error': f'Setup failed: {str(e)}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def health_check(self, request, pk=None):
        """Perform health check on WABA account"""
        waba_account = self.get_object()
        
        try:
            service = WhatsAppService()
            result = service.health_check_waba_account(waba_account)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': f'Health check failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'], url_path='analytics')
    def analytics(self, request, pk=None):
        """Get analytics for WABA account"""
        waba_account = self.get_object()
        
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        try:
            service = WhatsAppService()
            analytics_data = service.get_waba_account_analytics(
                waba_account, start_date, end_date
            )
            return Response(analytics_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': f'Analytics failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Send a message via this WABA account"""
        waba_account = self.get_object()
        
        # Add WABA account ID to request data
        request.data['waba_account_id'] = waba_account.id
        
        serializer = WhatsAppMessageSendSerializer(data=request.data)
        if serializer.is_valid():
            try:
                service = WhatsAppService()
                validated_data = serializer.validated_data
                
                # Get phone number
                phone_number = waba_account.get_primary_phone_number()
                if not phone_number:
                    return Response(
                        {'error': 'No active phone number found for this account'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Send message based on type
                message_type = validated_data['message_type']
                to_phone = validated_data['to_phone_number']
                
                if message_type == 'text':
                    response = service.send_text_message(
                        waba_account=waba_account,
                        phone_number=phone_number,
                        to_phone=to_phone,
                        text_content=validated_data['text_content'],
                        customer_id=validated_data.get('customer_id'),
                        campaign_id=validated_data.get('campaign_id')
                    )
                
                elif message_type == 'template':
                    response = service.send_template_message(
                        waba_account=waba_account,
                        phone_number=phone_number,
                        to_phone=to_phone,
                        template=validated_data['template'],
                        template_params=validated_data.get('template_params'),
                        customer_id=validated_data.get('customer_id'),
                        campaign_id=validated_data.get('campaign_id')
                    )
                
                elif message_type == 'interactive':
                    response = service.send_interactive_message(
                        waba_account=waba_account,
                        phone_number=phone_number,
                        to_phone=to_phone,
                        flow=validated_data['flow'],
                        flow_token=validated_data.get('flow_token'),
                        customer_id=validated_data.get('customer_id'),
                        campaign_id=validated_data.get('campaign_id')
                    )
                
                return Response(response, status=status.HTTP_200_OK)
                
            except WhatsAppAPIError as e:
                return Response(
                    {'error': f'Failed to send message: {str(e)}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                return Response(
                    {'error': f'Unexpected error: {str(e)}'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WhatsAppPhoneNumberViewSet(viewsets.ModelViewSet):
    """ViewSet for managing WhatsApp phone numbers"""
    
    queryset = WhatsAppPhoneNumber.objects.all()
    serializer_class = WhatsAppPhoneNumberSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter phone numbers based on user permissions"""
        queryset = super().get_queryset()
        
        # Filter by WABA account ownership
        waba_account_id = self.request.query_params.get('waba_account')
        if waba_account_id:
            queryset = queryset.filter(waba_account_id=waba_account_id)
        
        # If user is not admin, filter by WABA account ownership
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                waba_account__created_by=self.request.user
            )
        
        return queryset.select_related('waba_account')


class WhatsAppMessageTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for managing WhatsApp message templates"""
    
    queryset = WhatsAppMessageTemplate.objects.all()
    serializer_class = WhatsAppMessageTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter templates based on user permissions"""
        queryset = super().get_queryset()
        
        # Filter by WABA account
        waba_account_id = self.request.query_params.get('waba_account')
        if waba_account_id:
            queryset = queryset.filter(waba_account_id=waba_account_id)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # If user is not admin, filter by WABA account ownership
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                waba_account__created_by=self.request.user
            )
        
        return queryset.select_related('waba_account', 'created_by')
    
    @action(detail=True, methods=['post'])
    def submit_for_approval(self, request, pk=None):
        """Submit template for Meta approval"""
        template = self.get_object()
        
        try:
            service = WhatsAppService()
            response = service.create_message_template(
                template.waba_account, 
                {
                    'name': template.name,
                    'category': template.category,
                    'language': template.language,
                    'header_text': template.header_text,
                    'body_text': template.body_text,
                    'footer_text': template.footer_text,
                    'components': template.components
                }
            )
            
            return Response({
                'message': 'Template submitted for approval successfully',
                'meta_response': response
            }, status=status.HTTP_200_OK)
            
        except WhatsAppAPIError as e:
            return Response(
                {'error': f'Failed to submit template: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Unexpected error: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WhatsAppMessageViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing WhatsApp messages (read-only)"""
    
    queryset = WhatsAppMessage.objects.all()
    serializer_class = WhatsAppMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['direction', 'message_type', 'status', 'waba_account', 'phone_number']
    search_fields = ['message_id', 'to_phone_number', 'from_phone_number']
    ordering_fields = ['created_at', 'sent_at', 'delivered_at', 'read_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter messages based on user permissions"""
        queryset = super().get_queryset()
        
        # If user is not admin, filter by WABA account ownership
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                waba_account__created_by=self.request.user
            )
        
        return queryset.select_related(
            'waba_account', 'phone_number', 'template', 'campaign', 'customer'
        )


class WhatsAppWebhookEventViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing WhatsApp webhook events (read-only)"""
    
    queryset = WhatsAppWebhookEvent.objects.all()
    serializer_class = WhatsAppWebhookEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['event_type', 'processed', 'waba_account']
    ordering = ['-received_at']
    
    def get_queryset(self):
        """Filter webhook events based on user permissions"""
        queryset = super().get_queryset()
        
        # If user is not admin, filter by WABA account ownership
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                waba_account__created_by=self.request.user
            )
        
        return queryset.select_related('waba_account', 'message')


class WhatsAppFlowViewSet(viewsets.ModelViewSet):
    """ViewSet for managing WhatsApp Flows"""
    
    queryset = WhatsAppFlow.objects.all()
    serializer_class = WhatsAppFlowSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter flows based on user permissions"""
        queryset = super().get_queryset()
        
        # Filter by WABA account
        waba_account_id = self.request.query_params.get('waba_account')
        if waba_account_id:
            queryset = queryset.filter(waba_account_id=waba_account_id)
        
        # If user is not admin, filter by WABA account ownership
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                waba_account__created_by=self.request.user
            )
        
        return queryset.select_related('waba_account', 'created_by')
    
    def perform_create(self, serializer):
        """Create a new WhatsApp Flow"""
        serializer.save(created_by=self.request.user)


class WhatsAppWebhookView(viewsets.ViewSet):
    """ViewSet for handling WhatsApp webhook events"""
    
    permission_classes = []  # No authentication required for webhooks
    parser_classes = [JSONParser]
    
    @action(detail=False, methods=['get', 'post'], url_path='webhook')
    def webhook(self, request):
        """Handle WhatsApp webhook events"""
        
        # Handle webhook verification (GET request)
        if request.method == 'GET':
            hub_mode = request.GET.get('hub.mode')
            hub_challenge = request.GET.get('hub.challenge')
            hub_verify_token = request.GET.get('hub.verify_token')
            
            # Find WABA account with matching verify token
            try:
                waba_account = WhatsAppBusinessAccount.objects.get(
                    webhook_verify_token=hub_verify_token,
                    is_active=True
                )
                
                if hub_mode == 'subscribe':
                    return Response(hub_challenge, status=status.HTTP_200_OK)
                else:
                    return Response('Invalid mode', status=status.HTTP_400_BAD_REQUEST)
                    
            except WhatsAppBusinessAccount.DoesNotExist:
                return Response('Invalid verify token', status=status.HTTP_403_FORBIDDEN)
        
        # Handle webhook events (POST request)
        elif request.method == 'POST':
            try:
                service = WhatsAppService()
                webhook_event = service.process_webhook_event(request.data)
                
                return Response({
                    'status': 'success',
                    'event_id': webhook_event.id
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                logger.error(f"Webhook processing failed: {e}")
                return Response(
                    {'error': 'Webhook processing failed'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response('Method not allowed', status=status.HTTP_405_METHOD_NOT_ALLOWED)


class WhatsAppAnalyticsViewSet(viewsets.ViewSet):
    """ViewSet for WhatsApp analytics and reporting"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        """Get dashboard analytics"""
        user = request.user
        
        # Base queryset
        if user.is_staff:
            waba_accounts = WhatsAppBusinessAccount.objects.filter(is_deleted=False)
        else:
            waba_accounts = WhatsAppBusinessAccount.objects.filter(
                created_by=user, is_deleted=False
            )
        
        # Get summary statistics
        total_accounts = waba_accounts.count()
        active_accounts = waba_accounts.filter(is_active=True, status='verified').count()
        
        # Get message statistics for last 30 days
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        recent_messages = WhatsAppMessage.objects.filter(
            waba_account__in=waba_accounts,
            created_at__gte=thirty_days_ago
        )
        
        total_messages = recent_messages.count()
        sent_messages = recent_messages.filter(direction='outbound').count()
        received_messages = recent_messages.filter(direction='inbound').count()
        
        # Get delivery statistics
        delivered_messages = recent_messages.filter(status='delivered').count()
        read_messages = recent_messages.filter(status='read').count()
        failed_messages = recent_messages.filter(status='failed').count()
        
        # Get template statistics
        total_templates = WhatsAppMessageTemplate.objects.filter(
            waba_account__in=waba_accounts
        ).count()
        approved_templates = WhatsAppMessageTemplate.objects.filter(
            waba_account__in=waba_accounts, status='approved'
        ).count()
        
        return Response({
            'accounts': {
                'total': total_accounts,
                'active': active_accounts
            },
            'messages_30_days': {
                'total': total_messages,
                'sent': sent_messages,
                'received': received_messages,
                'delivered': delivered_messages,
                'read': read_messages,
                'failed': failed_messages,
                'delivery_rate': (delivered_messages / sent_messages * 100) if sent_messages > 0 else 0,
                'read_rate': (read_messages / delivered_messages * 100) if delivered_messages > 0 else 0
            },
            'templates': {
                'total': total_templates,
                'approved': approved_templates
            }
        }, status=status.HTTP_200_OK)
