"""
Views for Email Provider API endpoints
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import EmailProviderConfig, EmailProviderHealthLog, EmailProviderUsageLog, EmailProviderTestResult
from .serializers import (
    EmailProviderConfigSerializer, EmailProviderConfigCreateSerializer, EmailProviderConfigUpdateSerializer,
    EmailProviderHealthLogSerializer, EmailProviderUsageLogSerializer, EmailProviderTestResultSerializer,
    EmailProviderTestSerializer, EmailSendSerializer, EmailProviderStatisticsSerializer
)
from .services import email_provider_service
from .utils import clear_provider_cache


class EmailProviderConfigViewSet(viewsets.ModelViewSet):
    """ViewSet for EmailProviderConfig management"""
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get queryset based on user permissions"""
        return EmailProviderConfig.objects.filter(is_deleted=False).order_by('priority', 'name')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return EmailProviderConfigCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return EmailProviderConfigUpdateSerializer
        return EmailProviderConfigSerializer
    
    def perform_create(self, serializer):
        """Create provider with user context"""
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        """Update provider and clear cache"""
        instance = serializer.save()
        clear_provider_cache(instance.id)
    
    def perform_destroy(self, instance):
        """Soft delete provider"""
        instance.soft_delete(user=self.request.user)
        clear_provider_cache(instance.id)
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Test email provider configuration"""
        provider = self.get_object()
        serializer = EmailProviderTestSerializer(data=request.data, context={'provider': provider})
        
        if serializer.is_valid():
            test_type = serializer.validated_data.get('test_type', 'send_test')
            test_email = serializer.validated_data.get('test_email')
            
            try:
                if test_type == 'send_test':
                    result = email_provider_service.test_provider(provider, test_email)
                else:
                    result = email_provider_service._check_provider_health(provider)
                    result = {
                        'success': result[0],
                        'error': result[2] if not result[0] else '',
                        'response_time': result[1]
                    }
                
                # Log test result
                EmailProviderTestResult.objects.create(
                    provider=provider,
                    test_type=test_type,
                    status='success' if result['success'] else 'failed',
                    message=result.get('error', 'Test completed successfully') if not result['success'] else 'Test passed',
                    response_time=result.get('response_time', 0),
                    test_data={'test_email': test_email} if test_email else {}
                )
                
                return Response({
                    'success': result['success'],
                    'message': result.get('error', 'Test completed successfully') if not result['success'] else 'Test passed',
                    'response_time': result.get('response_time', 0),
                    'test_type': test_type
                })
                
            except Exception as e:
                EmailProviderTestResult.objects.create(
                    provider=provider,
                    test_type=test_type,
                    status='failed',
                    message=str(e),
                    test_data={'test_email': test_email} if test_email else {}
                )
                
                return Response({
                    'success': False,
                    'message': str(e),
                    'test_type': test_type
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def health_check(self, request, pk=None):
        """Perform health check on specific provider"""
        provider = self.get_object()
        
        try:
            is_healthy, response_time, error_message = email_provider_service._check_provider_health(provider)
            
            if is_healthy:
                provider.update_health_status('healthy')
            else:
                provider.update_health_status('unhealthy', error_message)
            
            return Response({
                'healthy': is_healthy,
                'response_time': response_time,
                'error_message': error_message,
                'status': provider.health_status
            })
            
        except Exception as e:
            return Response({
                'healthy': False,
                'error_message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def send_email(self, request):
        """Send email using best available provider"""
        serializer = EmailSendSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                result = email_provider_service.send_email(
                    to_emails=serializer.validated_data['to_emails'],
                    subject=serializer.validated_data['subject'],
                    html_content=serializer.validated_data.get('html_content', ''),
                    text_content=serializer.validated_data.get('text_content', ''),
                    from_email=serializer.validated_data.get('from_email'),
                    from_name=serializer.validated_data.get('from_name'),
                    reply_to=serializer.validated_data.get('reply_to'),
                    cc_emails=serializer.validated_data.get('cc_emails'),
                    bcc_emails=serializer.validated_data.get('bcc_emails')
                )
                
                if result['success']:
                    return Response(result)
                else:
                    return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
            except Exception as e:
                return Response({
                    'success': False,
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get statistics for all providers"""
        try:
            stats = email_provider_service.get_provider_statistics()
            serializer = EmailProviderStatisticsSerializer(stats.values(), many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def health_check_all(self, request):
        """Perform health check on all providers"""
        try:
            results = email_provider_service.health_check_all_providers()
            return Response(results)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmailProviderHealthLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for EmailProviderHealthLog (read-only)"""
    
    permission_classes = [IsAuthenticated]
    serializer_class = EmailProviderHealthLogSerializer
    
    def get_queryset(self):
        """Get health logs with optional filtering"""
        queryset = EmailProviderHealthLog.objects.all().order_by('-created_at')
        
        provider_id = self.request.query_params.get('provider_id')
        if provider_id:
            queryset = queryset.filter(provider_id=provider_id)
        
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
        
        return queryset


class EmailProviderUsageLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for EmailProviderUsageLog (read-only)"""
    
    permission_classes = [IsAuthenticated]
    serializer_class = EmailProviderUsageLogSerializer
    
    def get_queryset(self):
        """Get usage logs with optional filtering"""
        queryset = EmailProviderUsageLog.objects.all().order_by('-date')
        
        provider_id = self.request.query_params.get('provider_id')
        if provider_id:
            queryset = queryset.filter(provider_id=provider_id)
        
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        return queryset


class EmailProviderTestResultViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for EmailProviderTestResult (read-only)"""
    
    permission_classes = [IsAuthenticated]
    serializer_class = EmailProviderTestResultSerializer
    
    def get_queryset(self):
        """Get test results with optional filtering"""
        queryset = EmailProviderTestResult.objects.all().order_by('-created_at')
        
        provider_id = self.request.query_params.get('provider_id')
        if provider_id:
            queryset = queryset.filter(provider_id=provider_id)
        
        test_type = self.request.query_params.get('test_type')
        if test_type:
            queryset = queryset.filter(test_type=test_type)
        
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset