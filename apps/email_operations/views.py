from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, F
from django.utils import timezone
from datetime import timedelta, date

from .models import EmailMessage, EmailQueue, EmailTracking, EmailDeliveryReport, EmailAnalytics
from .serializers import (
    EmailMessageSerializer, EmailMessageCreateSerializer, EmailMessageUpdateSerializer,
    EmailQueueSerializer, EmailTrackingSerializer, EmailDeliveryReportSerializer,
    EmailAnalyticsSerializer, BulkEmailSerializer, ScheduledEmailSerializer,
    EmailStatsSerializer, EmailCampaignStatsSerializer
)
from .services import EmailOperationsService


class EmailMessageViewSet(viewsets.ModelViewSet):
    """ViewSet for managing email messages"""
    
    queryset = EmailMessage.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return EmailMessageCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return EmailMessageUpdateSerializer
        return EmailMessageSerializer
    
    def get_queryset(self):
        """Filter email messages based on query parameters"""
        queryset = super().get_queryset()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter by campaign
        campaign_id = self.request.query_params.get('campaign_id')
        if campaign_id:
            queryset = queryset.filter(campaign_id=campaign_id)
        
        # Filter by template
        template_id = self.request.query_params.get('template_id')
        if template_id:
            queryset = queryset.filter(template_id=template_id)
        
        # Filter by recipient
        to_email = self.request.query_params.get('to_email')
        if to_email:
            queryset = queryset.filter(to_email__icontains=to_email)
        
        # Filter by sender
        from_email = self.request.query_params.get('from_email')
        if from_email:
            queryset = queryset.filter(from_email__icontains=from_email)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        # Search by subject
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(subject__icontains=search)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """Set created_by when creating a new email message"""
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        """Set updated_by when updating an email message"""
        serializer.save(updated_by=self.request.user)
    
    def perform_destroy(self, instance):
        """Soft delete the email message"""
        instance.soft_delete()
        instance.deleted_by = self.request.user
        instance.save(update_fields=['deleted_by'])
    
    @action(detail=False, methods=['post'])
    def send_bulk(self, request):
        """Send bulk emails"""
        serializer = BulkEmailSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        service = EmailOperationsService()
        service.context = {'user': request.user}
        
        result = service.send_bulk_emails(**serializer.validated_data)
        
        if result['success']:
            return Response(result, status=status.HTTP_201_CREATED)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def send_scheduled(self, request):
        """Schedule an email for future sending"""
        serializer = ScheduledEmailSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        service = EmailOperationsService()
        service.context = {'user': request.user}
        
        result = service.schedule_email(**serializer.validated_data)
        
        if result['success']:
            return Response(result, status=status.HTTP_201_CREATED)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def resend(self, request, pk=None):
        """Resend a failed email"""
        email_message = self.get_object()
        
        if email_message.status not in ['failed', 'bounced']:
            return Response(
                {'error': 'Email can only be resent if it failed or bounced'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        service = EmailOperationsService()
        service.context = {'user': request.user}
        
        # Reset status and retry
        email_message.status = 'pending'
        email_message.retry_count = 0
        email_message.error_message = None
        email_message.save()
        
        result = service._send_email_message(email_message)
        
        if result['success']:
            return Response({'message': 'Email resent successfully'})
        else:
            return Response(
                {'error': result.get('error', 'Failed to resend email')},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a pending email"""
        email_message = self.get_object()
        
        if email_message.status not in ['pending', 'sending']:
            return Response(
                {'error': 'Email can only be cancelled if it is pending or sending'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        email_message.status = 'cancelled'
        email_message.save()
        
        # Update queue if exists
        try:
            queue_entry = EmailQueue.objects.get(email_message=email_message)
            queue_entry.status = 'cancelled'
            queue_entry.save()
        except EmailQueue.DoesNotExist:
            pass
        
        return Response({'message': 'Email cancelled successfully'})
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get email statistics"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        campaign_id = request.query_params.get('campaign_id')
        
        service = EmailOperationsService()
        service.context = {'user': request.user}
        
        stats = service.get_email_statistics(start_date, end_date, campaign_id)
        
        if 'error' in stats:
            return Response(stats, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def campaign_stats(self, request):
        """Get campaign statistics"""
        campaign_id = request.query_params.get('campaign_id')
        
        if not campaign_id:
            return Response(
                {'error': 'campaign_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get campaign emails
        emails = EmailMessage.objects.filter(
            campaign_id=campaign_id,
            is_deleted=False
        )
        
        # Calculate statistics
        total_emails = emails.count()
        sent_emails = emails.filter(status='sent').count()
        delivered_emails = emails.filter(status='delivered').count()
        
        # Get tracking data
        tracking_events = EmailTracking.objects.filter(
            email_message__in=emails
        )
        
        opened_emails = tracking_events.filter(event_type='opened').values('email_message').distinct().count()
        clicked_emails = tracking_events.filter(event_type='clicked').values('email_message').distinct().count()
        bounced_emails = tracking_events.filter(event_type='bounced').values('email_message').distinct().count()
        complained_emails = tracking_events.filter(event_type='complained').values('email_message').distinct().count()
        unsubscribed_emails = tracking_events.filter(event_type='unsubscribed').values('email_message').distinct().count()
        
        # Calculate rates
        delivery_rate = (delivered_emails / sent_emails * 100) if sent_emails > 0 else 0
        open_rate = (opened_emails / delivered_emails * 100) if delivered_emails > 0 else 0
        click_rate = (clicked_emails / delivered_emails * 100) if delivered_emails > 0 else 0
        bounce_rate = (bounced_emails / sent_emails * 100) if sent_emails > 0 else 0
        complaint_rate = (complained_emails / sent_emails * 100) if sent_emails > 0 else 0
        unsubscribe_rate = (unsubscribed_emails / sent_emails * 100) if sent_emails > 0 else 0
        
        # Get date range
        start_date = emails.aggregate(start=models.Min('created_at'))['start']
        end_date = emails.aggregate(end=models.Max('created_at'))['end']
        
        return Response({
            'campaign_id': campaign_id,
            'campaign_name': campaign_id,  # You might want to get this from a campaign model
            'total_emails': total_emails,
            'sent_emails': sent_emails,
            'delivered_emails': delivered_emails,
            'opened_emails': opened_emails,
            'clicked_emails': clicked_emails,
            'bounced_emails': bounced_emails,
            'complained_emails': complained_emails,
            'unsubscribed_emails': unsubscribed_emails,
            'delivery_rate': round(delivery_rate, 2),
            'open_rate': round(open_rate, 2),
            'click_rate': round(click_rate, 2),
            'bounce_rate': round(bounce_rate, 2),
            'complaint_rate': round(complaint_rate, 2),
            'unsubscribe_rate': round(unsubscribe_rate, 2),
            'start_date': start_date,
            'end_date': end_date
        })


class EmailQueueViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing email queue"""
    
    queryset = EmailQueue.objects.all()
    serializer_class = EmailQueueSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter queue entries based on query parameters"""
        queryset = super().get_queryset()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter by scheduled time
        scheduled_after = self.request.query_params.get('scheduled_after')
        scheduled_before = self.request.query_params.get('scheduled_before')
        
        if scheduled_after:
            queryset = queryset.filter(scheduled_for__gte=scheduled_after)
        if scheduled_before:
            queryset = queryset.filter(scheduled_for__lte=scheduled_before)
        
        return queryset.order_by('scheduled_for', 'priority')
    
    @action(detail=False, methods=['post'])
    def process(self, request):
        """Process pending emails in the queue"""
        service = EmailOperationsService()
        service.context = {'user': request.user}
        
        result = service.process_email_queue()
        
        if result['success']:
            return Response(result)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """Retry a failed queue entry"""
        queue_entry = self.get_object()
        
        if queue_entry.status != 'failed':
            return Response(
                {'error': 'Only failed queue entries can be retried'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Reset status and reschedule
        queue_entry.status = 'queued'
        queue_entry.scheduled_for = timezone.now()
        queue_entry.last_error = None
        queue_entry.save()
        
        return Response({'message': 'Queue entry scheduled for retry'})


class EmailTrackingViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing email tracking events"""
    
    queryset = EmailTracking.objects.all()
    serializer_class = EmailTrackingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter tracking events based on query parameters"""
        queryset = super().get_queryset()
        
        # Filter by email message
        email_message_id = self.request.query_params.get('email_message_id')
        if email_message_id:
            queryset = queryset.filter(email_message_id=email_message_id)
        
        # Filter by event type
        event_type = self.request.query_params.get('event_type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(event_time__gte=start_date)
        if end_date:
            queryset = queryset.filter(event_time__lte=end_date)
        
        return queryset.order_by('-event_time')


class EmailDeliveryReportViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing email delivery reports"""
    
    queryset = EmailDeliveryReport.objects.all()
    serializer_class = EmailDeliveryReportSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter delivery reports based on query parameters"""
        queryset = super().get_queryset()
        
        # Filter by email message
        email_message_id = self.request.query_params.get('email_message_id')
        if email_message_id:
            queryset = queryset.filter(email_message_id=email_message_id)
        
        # Filter by provider
        provider_name = self.request.query_params.get('provider_name')
        if provider_name:
            queryset = queryset.filter(provider_name=provider_name)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(reported_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(reported_at__lte=end_date)
        
        return queryset.order_by('-reported_at')


class EmailAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing email analytics"""
    
    queryset = EmailAnalytics.objects.all()
    serializer_class = EmailAnalyticsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter analytics based on query parameters"""
        queryset = super().get_queryset()
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        # Filter by period type
        period_type = self.request.query_params.get('period_type')
        if period_type:
            queryset = queryset.filter(period_type=period_type)
        
        # Filter by campaign
        campaign_id = self.request.query_params.get('campaign_id')
        if campaign_id:
            queryset = queryset.filter(campaign_id=campaign_id)
        
        # Filter by template
        template_id = self.request.query_params.get('template_id')
        if template_id:
            queryset = queryset.filter(template_id=template_id)
        
        return queryset.order_by('-date')
