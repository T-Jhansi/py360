from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
# --- ADD THIS LINE ---
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db.models import Q, Count
from django.utils import timezone

from .models import EmailTemplate, EmailTemplateCategory, EmailTemplateTag, EmailTemplateVersion
from .serializers import (
    EmailTemplateSerializer, EmailTemplateCreateSerializer, EmailTemplateUpdateSerializer,
    EmailTemplateCategorySerializer, EmailTemplateTagSerializer, EmailTemplateVersionSerializer,
    EmailTemplateRenderSerializer
)


class SoftDeleteMixin:
    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.deleted_by = self.request.user
        instance.save()

class StatusControlMixin:
    @action(detail=True, methods=['post'], url_path='activate')
    def activate(self, request, pk=None):
        instance = self.get_object()
        instance.is_active = True
        instance.updated_by = request.user
        instance.save()
        return Response({'message': f'{instance.__class__.__name__} activated successfully.'})

    @action(detail=True, methods=['post'], url_path='deactivate')
    def deactivate(self, request, pk=None):
        instance = self.get_object()
        instance.is_active = False
        instance.updated_by = request.user
        instance.save()
        return Response({'message': f'{instance.__class__.__name__} deactivated successfully.'})


class EmailTemplateCategoryViewSet(SoftDeleteMixin, StatusControlMixin, viewsets.ModelViewSet):
    queryset = EmailTemplateCategory.objects.filter(is_deleted=False)
    serializer_class = EmailTemplateCategorySerializer
    permission_classes = [IsAuthenticated]
    # This ViewSet will use the global settings, which is fine.

    def get_queryset(self):
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=(is_active.lower() == 'true'))
        return queryset.order_by('name')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class EmailTemplateTagViewSet(SoftDeleteMixin, StatusControlMixin, viewsets.ModelViewSet):
    queryset = EmailTemplateTag.objects.filter(is_deleted=False)
    serializer_class = EmailTemplateTagSerializer
    permission_classes = [IsAuthenticated]
    # This ViewSet will use the global settings, which is fine.

    def get_queryset(self):
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=(is_active.lower() == 'true'))
        return queryset.order_by('name')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class EmailTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for managing email templates."""
    queryset = EmailTemplate.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated]
    
    # --- THIS IS THE FIX ---
    # We explicitly tell this ViewSet to ONLY use JWT Token Authentication.
    # This prevents the browser-based SessionAuthentication from running
    # and causing the CSRF error.
    authentication_classes = [JWTAuthentication]

    def get_serializer_class(self):
        if self.action == 'create':
            return EmailTemplateCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return EmailTemplateUpdateSerializer
        return EmailTemplateSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        search = params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(subject__icontains=search)
            )
        status_filter = params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        category_id = params.get('category_id')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        tag_names = params.getlist('tags')
        if tag_names:
            queryset = queryset.filter(tags__name__in=tag_names).distinct()
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        instance.soft_delete(user=self.request.user)
    
    # ... (the rest of the class is the same) ...
    @action(detail=True, methods=['post'])
    def render(self, request, pk=None):
        template = self.get_object()
        serializer = EmailTemplateRenderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        context = serializer.validated_data.get('context', {})
        rendered_content = template.render_content(context)
        return Response(rendered_content)

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        original_template = self.get_object()
        new_template = original_template.duplicate(user=self.request.user)
        serializer = self.get_serializer(new_template)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='increment-usage')
    def increment_usage(self, request, pk=None):
        template = self.get_object()
        template.increment_usage()
        return Response({
            'message': 'Usage count incremented',
            'usage_count': template.usage_count,
            'last_used': template.last_used
        })

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        queryset = self.get_queryset()
        stats_data = {
            'total_templates': queryset.count(),
            'active_templates': queryset.filter(status='active').count(),
            'draft_templates': queryset.filter(status='draft').count(),
            'archived_templates': queryset.filter(status='archived').count(),
            'most_used_templates': EmailTemplateSerializer(queryset.order_by('-usage_count')[:5], many=True).data,
            'recent_templates': EmailTemplateSerializer(queryset.order_by('-created_at')[:5], many=True).data,
            'category_distribution': list(queryset.values('category__name').annotate(count=Count('id')).order_by('-count')),
            'type_distribution': list(queryset.values('template_type').annotate(count=Count('id')).order_by('-count'))
        }
        return Response(stats_data)


class EmailTemplateVersionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EmailTemplateVersion.objects.all()
    serializer_class = EmailTemplateVersionSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication] # Also good to add it here

    def get_queryset(self):
        queryset = super().get_queryset()
        template_id = self.request.query_params.get('template_id')
        if template_id:
            queryset = queryset.filter(template_id=template_id)
        return queryset.order_by('-version_number')

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        version = self.get_object()
        version.restore(user=request.user)
        return Response({'message': f'Template restored to version {version.version_number}'})
