from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Template
from .serializers import TemplateSerializer


class TemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for Template model"""
    
    queryset = Template.objects.all()
    serializer_class = TemplateSerializer
    
    def get_queryset(self):
        """Filter templates based on query parameters"""
        queryset = Template.objects.all()
        
        # Filter by channel if provided
        channel = self.request.query_params.get('channel', None)
        if channel:
            queryset = queryset.filter(channel=channel)
            
        # Filter by is_active if provided
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
            
        # Search by name if provided
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(subject__icontains=search) |
                Q(content__icontains=search)
            )
            
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def get_all_templates(self, request):
        """Get all templates with optional filtering"""
        try:
            templates = self.get_queryset()
            serializer = self.get_serializer(templates, many=True)
            
            return Response({
                'success': True,
                'message': 'Templates retrieved successfully',
                'data': serializer.data,
                'count': templates.count()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error retrieving templates: {str(e)}',
                'data': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def get_templates_by_channel(self, request):
        """Get templates filtered by channel"""
        channel = request.query_params.get('channel')
        if not channel:
            return Response({
                'success': False,
                'message': 'Channel parameter is required',
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            templates = Template.objects.filter(channel=channel, is_active=True)
            serializer = self.get_serializer(templates, many=True)
            
            return Response({
                'success': True,
                'message': f'Templates for channel {channel} retrieved successfully',
                'data': serializer.data,
                'count': templates.count()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error retrieving templates: {str(e)}',
                'data': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
