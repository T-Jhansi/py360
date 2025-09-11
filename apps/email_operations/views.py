"""
Views for Email Operations API endpoints
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.http import HttpResponse
import logging

from .models import EmailMessage, EmailQueue, EmailTracking, EmailDeliveryReport, EmailAnalytics
from .serializers import (
    EmailMessageSerializer, EmailMessageCreateSerializer, EmailBulkSendSerializer,
    EmailScheduledSendSerializer, EmailQueueSerializer, EmailQueueCreateSerializer,
    EmailTrackingSerializer, EmailDeliveryReportSerializer, EmailAnalyticsSerializer,
    EmailStatusSerializer, EmailTrackingDataSerializer, EmailAnalyticsSummarySerializer,
    EmailQueueStatusSerializer, EmailRetrySerializer
)
from .services import email_operations_service

logger = logging.getLogger(__name__)


class EmailMessageViewSet(viewsets.ModelViewSet):
    """ViewSet for EmailMessage management"""
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get queryset based on user permissions and filters"""
        queryset = EmailMessage.objects.filter(is_deleted=False)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by priority
        priority_filter = self.request.query_params.get('priority')
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)
        
        # Filter by template
        template_id = self.request.query_params.get('template_id')
        if template_id:
            queryset = queryset.filter(template_id=template_id)
        
        # Filter by campaign
        campaign_id = self.request.query_params.get('campaign_id')
        if campaign_id:
            queryset = queryset.filter(campaign_id=campaign_id)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        
        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(to_email__icontains=search) |
                Q(subject__icontains=search) |
                Q(campaign_id__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return EmailMessageCreateSerializer
        return EmailMessageSerializer
    
    def perform_create(self, serializer):
        """Create email message with user context"""
        email_data = serializer.validated_data
        
        # Send the email
        success, message, email_message = email_operations_service.send_single_email(
            to_email=email_data['to_email'],
            subject=email_data['subject'],
            html_content=email_data['html_content'],
            text_content=email_data.get('text_content', ''),
            from_email=email_data.get('from_email', ''),
            from_name=email_data.get('from_name', ''),
            reply_to=email_data.get('reply_to', ''),
            cc_emails=email_data.get('cc_emails', []),
            bcc_emails=email_data.get('bcc_emails', []),
            template_id=email_data.get('template'),
            template_context=email_data.get('template_context', {}),
            priority=email_data.get('priority', 'normal'),
            scheduled_at=email_data.get('scheduled_at'),
            campaign_id=email_data.get('campaign_id', ''),
            tags=email_data.get('tags', ''),
            max_retries=email_data.get('max_retries', 3),
            user=self.request.user
        )
        
        if not success:
            return Response({
                'success': False,
                'message': message
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def perform_destroy(self, instance):
        """Soft delete email message"""
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.deleted_by = self.request.user
        instance.save()
    
    @action(detail=False, methods=['post'])
    def send_bulk(self, request):
        """Send bulk emails"""
        serializer = EmailBulkSendSerializer(data=request.data)
        
        if serializer.is_valid():
            data = serializer.validated_data
            
            success, message, email_messages = email_operations_service.send_bulk_emails(
                recipients=data['recipients'],
                template_id=data['template_id'],
                from_email=data['from_email'],
                from_name=data.get('from_name', ''),
                reply_to=data.get('reply_to', ''),
                cc_emails=data.get('cc_emails', []),
                bcc_emails=data.get('bcc_emails', []),
                priority=data.get('priority', 'normal'),
                scheduled_at=data.get('scheduled_at'),
                campaign_id=data.get('campaign_id', ''),
                tags=data.get('tags', ''),
                max_retries=3,
                user=request.user
            )
            
            if success:
                return Response({
                    'success': True,
                    'message': message,
                    'emails_sent': len(email_messages),
                    'email_ids': [email.id for email in email_messages]
                })
            else:
                return Response({
                    'success': False,
                    'message': message
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def send_scheduled(self, request):
        """Send scheduled email"""
        serializer = EmailScheduledSendSerializer(data=request.data)
        
        if serializer.is_valid():
            data = serializer.validated_data
            
            success, message, email_message = email_operations_service.send_single_email(
                to_email=data['to_email'],
                subject="",  # Will be set from template
                html_content="",  # Will be set from template
                text_content="",  # Will be set from template
                from_email=data['from_email'],
                from_name=data.get('from_name', ''),
                reply_to=data.get('reply_to', ''),
                cc_emails=data.get('cc_emails', []),
                bcc_emails=data.get('bcc_emails', []),
                template_id=data['template_id'],
                template_context=data.get('context', {}),
                priority=data.get('priority', 'normal'),
                scheduled_at=data['scheduled_at'],
                campaign_id=data.get('campaign_id', ''),
                tags=data.get('tags', ''),
                max_retries=3,
                user=request.user
            )
            
            if success:
                return Response({
                    'success': True,
                    'message': message,
                    'email_id': email_message.id,
                    'message_id': email_message.message_id
                })
            else:
                return Response({
                    'success': False,
                    'message': message
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get email status"""
        email_message = self.get_object()
        status_data = email_operations_service.get_email_status(str(email_message.message_id))
        
        if status_data:
            serializer = EmailStatusSerializer(status_data)
            return Response(serializer.data)
        else:
            return Response({
                'error': 'Email not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['get'])
    def tracking(self, request, pk=None):
        """Get email tracking data"""
        email_message = self.get_object()
        tracking_data = email_operations_service.get_email_tracking_data(str(email_message.message_id))
        
        if tracking_data:
            serializer = EmailTrackingDataSerializer(tracking_data)
            return Response(serializer.data)
        else:
            return Response({
                'error': 'Email not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['post'])
    def retry_failed(self, request):
        """Retry failed emails"""
        serializer = EmailRetrySerializer(data=request.data)
        
        if serializer.is_valid():
            data = serializer.validated_data
            
            successful_retries, failed_retries = email_operations_service.retry_failed_emails(
                message_ids=data['message_ids'],
                force_retry=data.get('force_retry', False)
            )
            
            return Response({
                'success': True,
                'message': f'Retried {successful_retries} emails successfully, {failed_retries} failed',
                'successful_retries': successful_retries,
                'failed_retries': failed_retries
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmailQueueViewSet(viewsets.ModelViewSet):
    """ViewSet for EmailQueue management"""
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get queryset based on user permissions"""
        return EmailQueue.objects.filter(is_deleted=False).order_by('-created_at')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return EmailQueueCreateSerializer
        return EmailQueueSerializer
    
    def perform_create(self, serializer):
        """Create queue with user context"""
        serializer.save(created_by=self.request.user)
    
    def perform_destroy(self, instance):
        """Soft delete queue"""
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.deleted_by = self.request.user
        instance.save()
    
    @action(detail=True, methods=['post'])
    def start_processing(self, request, pk=None):
        """Start processing the queue"""
        queue = self.get_object()
        
        if queue.status != 'pending':
            return Response({
                'success': False,
                'message': f'Queue is already {queue.get_status_display().lower()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        queue.start_processing()
        
        return Response({
            'success': True,
            'message': 'Queue processing started'
        })
    
    @action(detail=True, methods=['post'])
    def stop_processing(self, request, pk=None):
        """Stop processing the queue"""
        queue = self.get_object()
        
        if queue.status != 'processing':
            return Response({
                'success': False,
                'message': 'Queue is not currently processing'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        queue.status = 'cancelled'
        queue.save(update_fields=['status'])
        
        return Response({
            'success': True,
            'message': 'Queue processing stopped'
        })
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """Get overall queue status"""
        status_data = email_operations_service.get_queue_status()
        serializer = EmailQueueStatusSerializer(status_data)
        return Response(serializer.data)


class EmailTrackingViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for EmailTracking (read-only)"""
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get tracking events with filters"""
        queryset = EmailTracking.objects.filter(email__is_deleted=False)
        
        # Filter by email
        email_id = self.request.query_params.get('email_id')
        if email_id:
            queryset = queryset.filter(email_id=email_id)
        
        # Filter by event type
        event_type = self.request.query_params.get('event_type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(event_timestamp__date__gte=date_from)
        
        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(event_timestamp__date__lte=date_to)
        
        return queryset.order_by('-event_timestamp')
    
    serializer_class = EmailTrackingSerializer


class EmailDeliveryReportViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for EmailDeliveryReport (read-only)"""
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get delivery reports with filters"""
        queryset = EmailDeliveryReport.objects.all()
        
        # Filter by provider
        provider = self.request.query_params.get('provider')
        if provider:
            queryset = queryset.filter(provider_name=provider)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(report_date__gte=date_from)
        
        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(report_date__lte=date_to)
        
        return queryset.order_by('-report_date')
    
    serializer_class = EmailDeliveryReportSerializer
    
    @action(detail=False, methods=['post'])
    def generate_report(self, request):
        """Generate delivery report for a specific date"""
        report_date = request.data.get('report_date')
        provider_name = request.data.get('provider_name')
        
        if not report_date:
            return Response({
                'error': 'report_date is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            report_date = timezone.datetime.strptime(report_date, '%Y-%m-%d').date()
            report = email_operations_service.generate_delivery_report(report_date, provider_name)
            
            serializer = EmailDeliveryReportSerializer(report)
            return Response(serializer.data)
            
        except ValueError:
            return Response({
                'error': 'Invalid date format. Use YYYY-MM-DD'
            }, status=status.HTTP_400_BAD_REQUEST)


class EmailAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for EmailAnalytics (read-only)"""
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get analytics with filters"""
        queryset = EmailAnalytics.objects.all()
        
        # Filter by template
        template_id = self.request.query_params.get('template_id')
        if template_id:
            queryset = queryset.filter(template_id=template_id)
        
        # Filter by campaign
        campaign_id = self.request.query_params.get('campaign_id')
        if campaign_id:
            queryset = queryset.filter(campaign_id=campaign_id)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(period_start__date__gte=date_from)
        
        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(period_end__date__lte=date_to)
        
        return queryset.order_by('-period_end')
    
    serializer_class = EmailAnalyticsSerializer
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get analytics summary for a period"""
        period_start = request.query_params.get('period_start')
        period_end = request.query_params.get('period_end')
        template_id = request.query_params.get('template_id')
        campaign_id = request.query_params.get('campaign_id')
        
        if not period_start or not period_end:
            return Response({
                'error': 'period_start and period_end are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            period_start = timezone.datetime.fromisoformat(period_start.replace('Z', '+00:00'))
            period_end = timezone.datetime.fromisoformat(period_end.replace('Z', '+00:00'))
            
            summary_data = email_operations_service.get_analytics_summary(
                period_start=period_start,
                period_end=period_end,
                template_id=int(template_id) if template_id else None,
                campaign_id=campaign_id or ""
            )
            
            serializer = EmailAnalyticsSummarySerializer(summary_data)
            return Response(serializer.data)
            
        except ValueError as e:
            return Response({
                'error': f'Invalid date format: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


# Tracking endpoints (public, no authentication required)
def track_email_open(request, message_id):
    """Track email open (public endpoint)"""
    ip_address = request.META.get('REMOTE_ADDR')
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    success = email_operations_service.track_email_open(
        message_id=message_id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if success:
        # Return 1x1 transparent pixel
        pixel_data = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x04\x01\x00\x3b'
        return HttpResponse(pixel_data, content_type='image/gif')
    else:
        return HttpResponse(status=404)


def track_email_click(request, message_id):
    """Track email click (public endpoint)"""
    clicked_url = request.GET.get('url', '')
    link_text = request.GET.get('text', '')
    ip_address = request.META.get('REMOTE_ADDR')
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    success = email_operations_service.track_email_click(
        message_id=message_id,
        clicked_url=clicked_url,
        link_text=link_text,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if success and clicked_url:
        # Redirect to the clicked URL
        from django.shortcuts import redirect
        return redirect(clicked_url)
    else:
        return HttpResponse(status=404)
