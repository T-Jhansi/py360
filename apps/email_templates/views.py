"""
Views for Email Templates API endpoints
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import EmailTemplate, EmailTemplateVersion, EmailTemplateCategory, EmailTemplateTag
from .serializers import (
    EmailTemplateSerializer, EmailTemplateCreateSerializer, EmailTemplateUpdateSerializer,
    EmailTemplateVersionSerializer, EmailTemplateCategorySerializer, EmailTemplateTagSerializer,
    EmailTemplatePreviewSerializer, EmailTemplateTestSerializer, EmailTemplateRenderSerializer,
    EmailTemplateBulkActionSerializer, EmailTemplateStatisticsSerializer
)
from apps.email_provider.services import email_provider_service


class EmailTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for EmailTemplate management"""
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get queryset based on user permissions and filters"""
        queryset = EmailTemplate.objects.filter(is_deleted=False)
        
        # Filter by template type
        template_type = self.request.query_params.get('template_type')
        if template_type:
            queryset = queryset.filter(template_type=template_type)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by tags
        tags = self.request.query_params.get('tags')
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',')]
            queryset = queryset.filter(tags__icontains=tag_list[0])
            for tag in tag_list[1:]:
                queryset = queryset.filter(tags__icontains=tag)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(subject__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return EmailTemplateCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return EmailTemplateUpdateSerializer
        return EmailTemplateSerializer
    
    def perform_create(self, serializer):
        """Create template with user context"""
        template = serializer.save(created_by=self.request.user)
        
        # Create initial version
        EmailTemplateVersion.objects.create(
            template=template,
            version_number=1,
            subject=template.subject,
            html_content=template.html_content,
            text_content=template.text_content,
            variables=template.variables,
            change_notes="Initial version",
            is_current=True,
            created_by=self.request.user
        )
    
    def perform_update(self, serializer):
        """Update template and create new version"""
        old_template = self.get_object()
        template = serializer.save()
        
        # Create new version if content changed
        if (old_template.subject != template.subject or 
            old_template.html_content != template.html_content or
            old_template.text_content != template.text_content or
            old_template.variables != template.variables):
            
            # Mark current version as not current
            EmailTemplateVersion.objects.filter(
                template=template, 
                is_current=True
            ).update(is_current=False)
            
            # Create new version
            new_version_number = EmailTemplateVersion.objects.filter(
                template=template
            ).count() + 1
            
            EmailTemplateVersion.objects.create(
                template=template,
                version_number=new_version_number,
                subject=template.subject,
                html_content=template.html_content,
                text_content=template.text_content,
                variables=template.variables,
                change_notes=f"Updated by {self.request.user.get_full_name()}",
                is_current=True,
                created_by=self.request.user
            )
    
    def perform_destroy(self, instance):
        """Soft delete template"""
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.deleted_by = self.request.user
        instance.save()
    
    @action(detail=True, methods=['post'])
    def preview(self, request, pk=None):
        """Preview template with provided context"""
        template = self.get_object()
        serializer = EmailTemplatePreviewSerializer(data=request.data)
        
        if serializer.is_valid():
            context = serializer.validated_data.get('context', {})
            rendered = template.render_content(context)
            
            return Response({
                'success': True,
                'rendered_content': rendered,
                'template_info': {
                    'name': template.name,
                    'subject': template.subject,
                    'template_type': template.template_type
                }
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Send test email using template"""
        template = self.get_object()
        serializer = EmailTemplateTestSerializer(data=request.data)
        
        if serializer.is_valid():
            test_email = serializer.validated_data['test_email']
            context = serializer.validated_data.get('context', {})
            
            try:
                # Render template
                rendered = template.render_content(context)
                
                # Send test email
                result = email_provider_service.send_email(
                    to_email=test_email,
                    subject=f"[TEST] {rendered['subject']}",
                    html_content=rendered['html_content'],
                    text_content=rendered['text_content']
                )
                
                if result['success']:
                    # Increment usage count
                    template.increment_usage()
                    
                    return Response({
                        'success': True,
                        'message': 'Test email sent successfully',
                        'provider_used': result.get('provider_name'),
                        'rendered_content': rendered
                    })
                else:
                    return Response({
                        'success': False,
                        'message': 'Failed to send test email',
                        'error': result.get('error')
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            except Exception as e:
                return Response({
                    'success': False,
                    'message': 'Error sending test email',
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def render(self, request, pk=None):
        """Render template with provided context"""
        template = self.get_object()
        serializer = EmailTemplateRenderSerializer(data=request.data)
        
        if serializer.is_valid():
            context = serializer.validated_data['context']
            rendered = template.render_content(context)
            
            return Response({
                'success': True,
                'rendered_content': rendered
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate template"""
        template = self.get_object()
        template.status = 'active'
        template.save(update_fields=['status'])
        
        return Response({
            'success': True,
            'message': 'Template activated successfully'
        })
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate template"""
        template = self.get_object()
        template.status = 'inactive'
        template.save(update_fields=['status'])
        
        return Response({
            'success': True,
            'message': 'Template deactivated successfully'
        })
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive template"""
        template = self.get_object()
        template.status = 'archived'
        template.save(update_fields=['status'])
        
        return Response({
            'success': True,
            'message': 'Template archived successfully'
        })
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Set template as default for its type"""
        template = self.get_object()
        
        # Remove default status from other templates of same type
        EmailTemplate.objects.filter(
            template_type=template.template_type,
            is_default=True
        ).update(is_default=False)
        
        # Set this template as default
        template.is_default = True
        template.save(update_fields=['is_default'])
        
        return Response({
            'success': True,
            'message': f'Template set as default for {template.get_template_type_display()}'
        })
    
    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """Perform bulk actions on templates"""
        serializer = EmailTemplateBulkActionSerializer(data=request.data)
        
        if serializer.is_valid():
            template_ids = serializer.validated_data['template_ids']
            action = serializer.validated_data['action']
            
            templates = EmailTemplate.objects.filter(
                id__in=template_ids,
                is_deleted=False
            )
            
            if action == 'activate':
                templates.update(status='active')
                message = f'Activated {templates.count()} templates'
            elif action == 'deactivate':
                templates.update(status='inactive')
                message = f'Deactivated {templates.count()} templates'
            elif action == 'archive':
                templates.update(status='archived')
                message = f'Archived {templates.count()} templates'
            elif action == 'delete':
                templates.update(
                    is_deleted=True,
                    deleted_at=timezone.now(),
                    deleted_by=request.user
                )
                message = f'Deleted {templates.count()} templates'
            
            return Response({
                'success': True,
                'message': message,
                'affected_count': templates.count()
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get template statistics"""
        queryset = self.get_queryset()
        
        # Basic counts
        total_templates = queryset.count()
        active_templates = queryset.filter(status='active').count()
        draft_templates = queryset.filter(status='draft').count()
        archived_templates = queryset.filter(status='archived').count()
        
        # Most used template
        most_used = queryset.order_by('-usage_count').first()
        most_used_name = most_used.name if most_used else 'None'
        
        # Total usage count
        total_usage = queryset.aggregate(
            total=Count('usage_count')
        )['total'] or 0
        
        # Templates by type
        templates_by_type = {}
        for template_type, _ in EmailTemplate.TEMPLATE_TYPES:
            count = queryset.filter(template_type=template_type).count()
            templates_by_type[template_type] = count
        
        # Recent templates
        recent_templates = queryset.order_by('-created_at')[:5].values(
            'id', 'name', 'template_type', 'status', 'created_at'
        )
        
        statistics = {
            'total_templates': total_templates,
            'active_templates': active_templates,
            'draft_templates': draft_templates,
            'archived_templates': archived_templates,
            'most_used_template': most_used_name,
            'total_usage_count': total_usage,
            'templates_by_type': templates_by_type,
            'recent_templates': list(recent_templates)
        }
        
        serializer = EmailTemplateStatisticsSerializer(statistics)
        return Response(serializer.data)


class EmailTemplateVersionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for EmailTemplateVersion (read-only)"""
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get versions for specific template"""
        template_id = self.request.query_params.get('template_id')
        if template_id:
            return EmailTemplateVersion.objects.filter(
                template_id=template_id,
                template__is_deleted=False
            ).order_by('-version_number')
        return EmailTemplateVersion.objects.filter(
            template__is_deleted=False
        ).order_by('-version_number')
    
    serializer_class = EmailTemplateVersionSerializer


class EmailTemplateCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for EmailTemplateCategory management"""
    
    permission_classes = [IsAuthenticated]
    queryset = EmailTemplateCategory.objects.all()
    serializer_class = EmailTemplateCategorySerializer
    
    def perform_create(self, serializer):
        """Create category with user context"""
        serializer.save(created_by=self.request.user)
    
    def perform_destroy(self, instance):
        """Soft delete category"""
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.deleted_by = self.request.user
        instance.save()


class EmailTemplateTagViewSet(viewsets.ModelViewSet):
    """ViewSet for EmailTemplateTag management"""
    
    permission_classes = [IsAuthenticated]
    queryset = EmailTemplateTag.objects.all()
    serializer_class = EmailTemplateTagSerializer
    
    def perform_create(self, serializer):
        """Create tag with user context"""
        serializer.save(created_by=self.request.user)
    
    def perform_destroy(self, instance):
        """Soft delete tag"""
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.deleted_by = self.request.user
        instance.save()
