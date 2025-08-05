from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from django.shortcuts import get_object_or_404
from apps.renewals.models import RenewalCase
from apps.case_logs.views import quick_edit_case_api
from apps.core.pagination import StandardResultsSetPagination
from .serializers import CaseTrackingSerializer, CaseDetailSerializer
from datetime import datetime, timedelta
from django.utils import timezone
from apps.files_upload.models import FileUpload

class CaseTrackingViewSet(viewsets.ReadOnlyModelViewSet):

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    lookup_field = 'id'
    lookup_url_kwarg = 'case_id'
    
    def get_queryset(self):
        return RenewalCase.objects.select_related(
            'customer',                   
            'policy',                      
            'policy__policy_type',       
            'channel_id',                  
            'assigned_to',                 
        ).prefetch_related(
            'customer__policies',          
        ).order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CaseDetailSerializer
        return CaseTrackingSerializer
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'cases': serializer.data,
            'total_count': queryset.count()
        })
    
    def retrieve(self, request, case_id=None, *args, **kwargs):
        queryset = self.get_queryset()
        case = get_object_or_404(queryset, id=case_id)
        serializer = self.get_serializer(case)

        return Response({
            'case': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        queryset = self.get_queryset()
        
        total_cases = queryset.count()
        
        status_stats = {}
        for status_choice in RenewalCase.STATUS_CHOICES:
            status_code = status_choice[0]
            status_label = status_choice[1]
            count = queryset.filter(status=status_code).count()
            status_stats[status_code] = {
                'label': status_label,
                'count': count
            }
        
        priority_stats = {}
        for priority_choice in RenewalCase.PRIORITY_CHOICES:
            priority_code = priority_choice[0]
            priority_label = priority_choice[1]
            count = queryset.filter(priority=priority_code).count()
            priority_stats[priority_code] = {
                'label': priority_label,
                'count': count
            }
        
    
        
        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_cases = queryset.filter(created_at__gte=seven_days_ago).count()
        
        return Response({
            'total_cases': total_cases,
            'status_breakdown': status_stats,
            'priority_breakdown': priority_stats,
            'recent_cases_7_days': recent_cases,
            'generated_at': timezone.now().isoformat()
        })
    
    @action(detail=False, methods=['get'])
    def batch_info(self, request):
        batch_code = request.query_params.get('batch_code')
        
        if batch_code:
            batch_cases = self.get_queryset().filter(batch_code=batch_code)
            
            if not batch_cases.exists():
                return Response(
                    {'error': f'No cases found for batch code: {batch_code}'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            total_cases = batch_cases.count()
            status_breakdown = {}
            
            for status_choice in RenewalCase.STATUS_CHOICES:
                status_code = status_choice[0]
                count = batch_cases.filter(status=status_code).count()
                if count > 0:
                    status_breakdown[status_code] = count
            
            try:
                file_upload = FileUpload.objects.filter(
                    processing_result__batch_code=batch_code
                ).first()
                
                upload_info = None
                if file_upload:
                    upload_info = {
                        'original_filename': file_upload.original_filename,
                        'upload_status': file_upload.upload_status,
                        'total_records': file_upload.total_records,
                        'successful_records': file_upload.successful_records,
                        'failed_records': file_upload.failed_records,
                        'created_at': file_upload.created_at.isoformat()
                    }
            except:
                upload_info = None
            
            return Response({
                'batch_code': batch_code,
                'total_cases': total_cases,
                'status_breakdown': status_breakdown,
                'upload_info': upload_info,
                'cases': CaseTrackingSerializer(batch_cases, many=True).data
            })
        
        else:
            from django.db.models import Count
            
            batch_summary = self.get_queryset().values('batch_code').annotate(
                case_count=Count('id')
            ).order_by('-case_count')
            
            return Response({
                'batches': list(batch_summary),
                'total_batches': len(batch_summary)
            })

    @action(detail=True, methods=['patch'], url_path='quick-edit')
    def quick_edit(self, request, case_id=None):
        return quick_edit_case_api(request, case_id)
