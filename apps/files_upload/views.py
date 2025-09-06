from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta

from .models import FileUpload
from .serializers import (
    FileUploadSerializer,
    FileUploadListSerializer,
    FileUploadDetailSerializer
)

class FileUploadViewSet(viewsets.ModelViewSet):
    """ViewSet for managing file uploads with comprehensive filtering and statistics"""
            
    queryset = FileUpload.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return FileUploadListSerializer
        elif self.action == 'retrieve':
            return FileUploadDetailSerializer
        return FileUploadSerializer

    def get_queryset(self):
        """Filter queryset based on query parameters"""
        queryset = super().get_queryset()

        # Get query parameters (handle both DRF and Django requests)
        query_params = getattr(self.request, 'query_params', self.request.GET)

        # Filter by upload status
        status_filter = query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(upload_status=status_filter)

        # Filter by date range
        start_date = query_params.get('start_date', None)
        end_date = query_params.get('end_date', None)

        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__gte=start_date)
            except ValueError:
                pass

        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__lte=end_date)
            except ValueError:
                pass

        # Filter by uploaded user
        uploaded_by = query_params.get('uploaded_by', None)
        if uploaded_by:
            queryset = queryset.filter(uploaded_by_id=uploaded_by)

        # Search by filename
        search = query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(original_filename__icontains=search) |
                Q(filename__icontains=search)
            )

        return queryset.order_by('-created_at')

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get file upload statistics"""
        queryset = self.get_queryset()

        # Overall statistics
        total_files = queryset.count()
        completed_files = queryset.filter(upload_status='completed').count()
        failed_files = queryset.filter(upload_status='failed').count()
        processing_files = queryset.filter(upload_status='processing').count()
        pending_files = queryset.filter(upload_status='pending').count()

        # Calculate totals
        total_records_processed = sum(f.total_records or 0 for f in queryset)
        total_successful_records = sum(f.successful_records or 0 for f in queryset)
        total_failed_records = sum(f.failed_records or 0 for f in queryset)

        # Calculate success rate
        overall_success_rate = 0
        if total_records_processed > 0:
            overall_success_rate = round((total_successful_records / total_records_processed) * 100, 2)

        # Recent uploads (last 7 days)
        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_uploads = queryset.filter(created_at__gte=seven_days_ago).count()

        # File size statistics
        total_file_size = sum(f.file_size or 0 for f in queryset)

        def format_file_size(size):
            """Format file size in human readable format"""
            if not size:
                return "0 B"
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"

        return Response({
            'total_files': total_files,
            'status_breakdown': {
                'completed': completed_files,
                'failed': failed_files,
                'processing': processing_files,
                'pending': pending_files,
                'partial': queryset.filter(upload_status='partial').count()
            },
            'records_statistics': {
                'total_records_processed': total_records_processed,
                'total_successful_records': total_successful_records,
                'total_failed_records': total_failed_records,
                'overall_success_rate': overall_success_rate
            },
            'file_size_statistics': {
                'total_file_size_bytes': total_file_size,
                'total_file_size_formatted': format_file_size(total_file_size),
                'average_file_size_bytes': total_file_size // total_files if total_files > 0 else 0,
                'average_file_size_formatted': format_file_size(total_file_size // total_files) if total_files > 0 else "0 B"
            },
            'recent_activity': {
                'uploads_last_7_days': recent_uploads
            }
        })

    @action(detail=True, methods=['get'])
    def processing_details(self, request, pk=None):
        """Get detailed processing information for a specific file"""
        file_upload = self.get_object()

        return Response({
            'id': file_upload.id,
            'original_filename': file_upload.original_filename,
            'upload_status': file_upload.upload_status,
            'processing_started_at': file_upload.processing_started_at,
            'processing_completed_at': file_upload.processing_completed_at,
            'processing_result': file_upload.processing_result,
            'error_details': file_upload.error_details,
            'total_records': file_upload.total_records,
            'successful_records': file_upload.successful_records,
            'failed_records': file_upload.failed_records,
            'success_rate': round((file_upload.successful_records / file_upload.total_records) * 100, 2) if file_upload.total_records > 0 else 0
        })

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent file uploads (last 10)"""
        recent_uploads = self.get_queryset()[:10]
        serializer = FileUploadListSerializer(recent_uploads, many=True)
        return Response(serializer.data)
