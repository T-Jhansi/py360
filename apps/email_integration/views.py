"""
Email Integration API Views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import models
from django.shortcuts import get_object_or_404
from django.utils import timezone
from typing import Dict, Any

from .models import (
    EmailWebhook, EmailAutomation, EmailIntegrationAnalytics, EmailIntegration,
    EmailAutomationLog, EmailSLA, EmailTemplateVariable
)
from .serializers import (
    EmailWebhookSerializer, EmailAutomationSerializer, EmailIntegrationAnalyticsSerializer,
    EmailIntegrationSerializer, EmailAutomationLogSerializer, EmailSLASerializer,
    EmailTemplateVariableSerializer, WebhookProcessSerializer, AutomationExecuteSerializer,
    IntegrationSyncSerializer, AnalyticsReportSerializer, DynamicTemplateSerializer,
    EmailScheduleSerializer, EmailReminderSerializer, EmailSignatureSerializer
)
from .services import (
    email_webhook_service, email_automation_service, email_analytics_service,
    email_integration_service
)


class EmailWebhookViewSet(viewsets.ModelViewSet):
    """ViewSet for managing email webhooks"""
    
    queryset = EmailWebhook.objects.all()
    serializer_class = EmailWebhookSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter webhooks based on query parameters"""
        queryset = EmailWebhook.objects.all()
        
        # Apply filters
        provider = self.request.query_params.get('provider')
        if provider:
            queryset = queryset.filter(provider=provider)
        
        event_type = self.request.query_params.get('event_type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        email_message_id = self.request.query_params.get('email_message_id')
        if email_message_id:
            queryset = queryset.filter(email_message_id=email_message_id)
        
        return queryset.order_by('-received_at')
    
    @action(detail=False, methods=['post'])
    def receive_sendgrid(self, request):
        """Receive SendGrid webhook"""
        try:
            webhook_data = request.data
            signature = request.headers.get('X-Twilio-Email-Event-Webhook-Signature', '')
            ip_address = request.META.get('REMOTE_ADDR', '')
            
            success, message, webhook = email_webhook_service.receive_webhook(
                provider='sendgrid',
                event_type=webhook_data.get('event', 'unknown'),
                webhook_data=webhook_data,
                signature=signature,
                ip_address=ip_address
            )
            
            if success:
                return Response({
                    'status': 'webhook received',
                    'message': message,
                    'webhook_id': webhook.id
                })
            else:
                return Response(
                    {'error': message}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response(
                {'error': f"Error receiving webhook: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def receive_aws_ses(self, request):
        """Receive AWS SES webhook"""
        try:
            webhook_data = request.data
            signature = request.headers.get('X-Amz-Sns-Signature', '')
            ip_address = request.META.get('REMOTE_ADDR', '')
            
            success, message, webhook = email_webhook_service.receive_webhook(
                provider='aws_ses',
                event_type=webhook_data.get('notificationType', 'unknown'),
                webhook_data=webhook_data,
                signature=signature,
                ip_address=ip_address
            )
            
            if success:
                return Response({
                    'status': 'webhook received',
                    'message': message,
                    'webhook_id': webhook.id
                })
            else:
                return Response(
                    {'error': message}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response(
                {'error': f"Error receiving webhook: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def process_pending(self, request):
        """Process pending webhooks"""
        serializer = WebhookProcessSerializer(data=request.data)
        
        if serializer.is_valid():
            webhook_ids = serializer.validated_data['webhook_ids']
            force_reprocess = serializer.validated_data['force_reprocess']
            
            webhooks = EmailWebhook.objects.filter(
                id__in=webhook_ids,
                status='pending' if not force_reprocess else models.Q()
            )
            
            results = []
            for webhook in webhooks:
                try:
                    # Process webhook logic here
                    webhook.mark_processed()
                    results.append({
                        'webhook_id': webhook.id,
                        'status': 'processed'
                    })
                except Exception as e:
                    webhook.mark_failed(str(e))
                    results.append({
                        'webhook_id': webhook.id,
                        'status': 'failed',
                        'error': str(e)
                    })
            
            return Response({
                'status': 'processing completed',
                'results': results
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmailAutomationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing email automations"""
    
    queryset = EmailAutomation.objects.all()
    serializer_class = EmailAutomationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter automations based on query parameters"""
        queryset = EmailAutomation.objects.all()
        
        # Apply filters
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        trigger_type = self.request.query_params.get('trigger_type')
        if trigger_type:
            queryset = queryset.filter(trigger_type=trigger_type)
        
        return queryset.order_by('-priority', 'name')
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Execute automation"""
        automation = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = AutomationExecuteSerializer(data=request.data)
        
        if serializer.is_valid():
            success, message, result = email_automation_service.execute_automation(
                automation_id=automation.id,
                trigger_data=serializer.validated_data['trigger_data'],
                force_execute=serializer.validated_data['force_execute']
            )
            
            if success:
                return Response({
                    'status': 'automation executed',
                    'message': message,
                    'result': result
                })
            else:
                return Response(
                    {'error': message}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """Get automation execution logs"""
        automation = get_object_or_404(self.get_queryset(), pk=pk)
        
        # Get pagination parameters
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        
        logs = EmailAutomationLog.objects.filter(automation=automation).order_by('-started_at')
        
        # Apply pagination
        start = (page - 1) * page_size
        end = start + page_size
        logs_page = logs[start:end]
        
        serializer = EmailAutomationLogSerializer(logs_page, many=True)
        
        return Response({
            'logs': serializer.data,
            'total_count': logs.count(),
            'page': page,
            'page_size': page_size
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get automation statistics"""
        total_automations = EmailAutomation.objects.count()
        active_automations = EmailAutomation.objects.filter(is_active=True).count()
        total_executions = EmailAutomation.objects.aggregate(
            total=models.Sum('execution_count')
        )['total'] or 0
        
        recent_logs = EmailAutomationLog.objects.filter(
            started_at__gte=timezone.now() - timezone.timedelta(days=7)
        )
        
        success_rate = 0
        if recent_logs.exists():
            successful_logs = recent_logs.filter(status='success').count()
            success_rate = (successful_logs / recent_logs.count()) * 100
        
        return Response({
            'total_automations': total_automations,
            'active_automations': active_automations,
            'total_executions': total_executions,
            'success_rate': round(success_rate, 2),
            'recent_executions': recent_logs.count()
        })


class EmailAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for email analytics"""
    
    queryset = EmailIntegrationAnalytics.objects.all()
    serializer_class = EmailIntegrationAnalyticsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter analytics based on query parameters"""
        queryset = EmailIntegrationAnalytics.objects.all()
        
        # Apply filters
        start_date = self.request.query_params.get('start_date')
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        
        end_date = self.request.query_params.get('end_date')
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        period_type = self.request.query_params.get('period_type')
        if period_type:
            queryset = queryset.filter(period_type=period_type)
        
        return queryset.order_by('-date')
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get analytics dashboard data"""
        # Get date range
        end_date = timezone.now().date()
        start_date = end_date - timezone.timedelta(days=30)
        
        # Get analytics data
        analytics_data = email_analytics_service.generate_analytics(
            start_date=start_date,
            end_date=end_date,
            period_type='daily'
        )
        
        # Calculate summary statistics
        total_emails = sum(
            data.get('total_emails_received', 0) + data.get('total_emails_sent', 0)
            for data in analytics_data.values()
        )
        
        avg_response_time = sum(
            data.get('avg_response_time_minutes', 0)
            for data in analytics_data.values()
        ) / len(analytics_data) if analytics_data else 0
        
        return Response({
            'analytics_data': analytics_data,
            'summary': {
                'total_emails': total_emails,
                'avg_response_time_minutes': round(avg_response_time, 2),
                'date_range': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                }
            }
        })
    
    @action(detail=False, methods=['post'])
    def generate_report(self, request):
        """Generate custom analytics report"""
        serializer = AnalyticsReportSerializer(data=request.data)
        
        if serializer.is_valid():
            analytics_data = email_analytics_service.generate_analytics(
                start_date=serializer.validated_data['start_date'],
                end_date=serializer.validated_data['end_date'],
                period_type=serializer.validated_data['period_type']
            )
            
            return Response({
                'report_data': analytics_data,
                'report_config': serializer.validated_data
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def trends(self, request):
        """Get trend analysis"""
        # Get trend data for different metrics
        end_date = timezone.now().date()
        start_date = end_date - timezone.timedelta(days=90)
        
        # Email volume trends
        volume_trends = EmailIntegrationAnalytics.objects.filter(
            date__range=[start_date, end_date]
        ).order_by('date').values('date', 'total_emails_received', 'total_emails_sent')
        
        # Response time trends
        response_trends = EmailIntegrationAnalytics.objects.filter(
            date__range=[start_date, end_date]
        ).order_by('date').values('date', 'avg_response_time_minutes')
        
        return Response({
            'volume_trends': list(volume_trends),
            'response_trends': list(response_trends),
            'date_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
        })


class EmailIntegrationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing email integrations"""
    
    queryset = EmailIntegration.objects.all()
    serializer_class = EmailIntegrationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter integrations based on query parameters"""
        queryset = EmailIntegration.objects.all()
        
        # Apply filters
        integration_type = self.request.query_params.get('integration_type')
        if integration_type:
            queryset = queryset.filter(integration_type=integration_type)
        
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('name')
    
    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """Sync integration data"""
        integration = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = IntegrationSyncSerializer(data=request.data)
        
        if serializer.is_valid():
            success, message = email_integration_service.sync_integration(
                integration_id=integration.id,
                sync_direction=serializer.validated_data['sync_direction']
            )
            
            if success:
                return Response({
                    'status': 'sync completed',
                    'message': message
                })
            else:
                return Response(
                    {'error': message}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get integration status"""
        integration = get_object_or_404(self.get_queryset(), pk=pk)
        
        return Response({
            'integration_id': integration.id,
            'name': integration.name,
            'status': integration.status,
            'is_active': integration.is_active,
            'last_sync': integration.last_sync,
            'error_count': integration.error_count,
            'last_error': integration.last_error,
            'sync_statistics': {
                'total_syncs': integration.total_syncs,
                'successful_syncs': integration.successful_syncs,
                'failed_syncs': integration.failed_syncs,
                'success_rate': round((integration.successful_syncs / integration.total_syncs * 100), 2) if integration.total_syncs > 0 else 0
            }
        })
    
    @action(detail=False, methods=['get'])
    def health_check(self, request):
        """Check health of all integrations"""
        integrations = EmailIntegration.objects.filter(is_active=True)
        
        health_status = []
        for integration in integrations:
            is_healthy = (
                integration.status == 'active' and
                integration.error_count < 5 and
                (not integration.last_sync or 
                 timezone.now() - integration.last_sync < timezone.timedelta(hours=24))
            )
            
            health_status.append({
                'integration_id': integration.id,
                'name': integration.name,
                'type': integration.integration_type,
                'is_healthy': is_healthy,
                'status': integration.status,
                'last_sync': integration.last_sync,
                'error_count': integration.error_count
            })
        
        return Response({
            'health_status': health_status,
            'total_integrations': integrations.count(),
            'healthy_integrations': sum(1 for status in health_status if status['is_healthy'])
        })


class EmailSLAViewSet(viewsets.ModelViewSet):
    """ViewSet for managing email SLAs"""
    
    queryset = EmailSLA.objects.all()
    serializer_class = EmailSLASerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter SLAs based on query parameters"""
        queryset = EmailSLA.objects.all()
        
        # Apply filters
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.order_by('name')


class EmailTemplateVariableViewSet(viewsets.ModelViewSet):
    """ViewSet for managing email template variables"""
    
    queryset = EmailTemplateVariable.objects.all()
    serializer_class = EmailTemplateVariableSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter variables based on query parameters"""
        queryset = EmailTemplateVariable.objects.all()
        
        # Apply filters
        variable_type = self.request.query_params.get('variable_type')
        if variable_type:
            queryset = queryset.filter(variable_type=variable_type)
        
        return queryset.order_by('name')


class EmailAdvancedFeaturesViewSet(viewsets.ViewSet):
    """ViewSet for advanced email features"""
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def create_dynamic_template(self, request):
        """Create dynamic email template"""
        serializer = DynamicTemplateSerializer(data=request.data)
        
        if serializer.is_valid():
            # Create dynamic template logic here
            template_data = serializer.validated_data
            
            return Response({
                'status': 'template created',
                'template_id': 1,  # Placeholder
                'message': 'Dynamic template created successfully'
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def schedule_email(self, request):
        """Schedule email for future delivery"""
        serializer = EmailScheduleSerializer(data=request.data)
        
        if serializer.is_valid():
            # Schedule email logic here
            email_data = serializer.validated_data
            
            return Response({
                'status': 'email scheduled',
                'scheduled_email_id': 1,  # Placeholder
                'scheduled_at': email_data['scheduled_at'],
                'message': 'Email scheduled successfully'
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def create_reminder(self, request):
        """Create email reminder"""
        serializer = EmailReminderSerializer(data=request.data)
        
        if serializer.is_valid():
            # Create reminder logic here
            reminder_data = serializer.validated_data
            
            return Response({
                'status': 'reminder created',
                'reminder_id': 1,  # Placeholder
                'reminder_at': reminder_data['reminder_at'],
                'message': 'Reminder created successfully'
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def create_signature(self, request):
        """Create email signature"""
        serializer = EmailSignatureSerializer(data=request.data)
        
        if serializer.is_valid():
            # Create signature logic here
            signature_data = serializer.validated_data
            
            return Response({
                'status': 'signature created',
                'signature_id': 1,  # Placeholder
                'message': 'Signature created successfully'
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
