"""
Serializers for Email Templates API endpoints
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import EmailTemplate, EmailTemplateVersion, EmailTemplateCategory, EmailTemplateTag

User = get_user_model()


class EmailTemplateCategorySerializer(serializers.ModelSerializer):
    """Serializer for EmailTemplateCategory"""
    
    class Meta:
        model = EmailTemplateCategory
        fields = ['id', 'name', 'description', 'color', 'icon', 'sort_order', 'created_at', 'updated_at']


class EmailTemplateTagSerializer(serializers.ModelSerializer):
    """Serializer for EmailTemplateTag"""
    
    class Meta:
        model = EmailTemplateTag
        fields = ['id', 'name', 'description', 'color', 'created_at', 'updated_at']


class EmailTemplateVersionSerializer(serializers.ModelSerializer):
    """Serializer for EmailTemplateVersion"""
    
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = EmailTemplateVersion
        fields = [
            'id', 'version_number', 'subject', 'html_content', 'text_content', 
            'variables', 'change_notes', 'is_current', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class EmailTemplateSerializer(serializers.ModelSerializer):
    """Serializer for EmailTemplate"""
    
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    template_type_display = serializers.CharField(source='get_template_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    # Related fields
    versions = EmailTemplateVersionSerializer(many=True, read_only=True)
    variables_list = serializers.SerializerMethodField()
    
    class Meta:
        model = EmailTemplate
        fields = [
            'id', 'name', 'subject', 'template_type', 'template_type_display',
            'status', 'status_display', 'html_content', 'text_content',
            'variables', 'variables_list', 'description', 'tags',
            'usage_count', 'last_used', 'is_default', 'requires_approval',
            'created_by_name', 'versions', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'usage_count', 'last_used', 'created_at', 'updated_at']
    
    def get_variables_list(self, obj):
        """Get list of available variables"""
        return obj.get_variables_list()


class EmailTemplateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating EmailTemplate"""
    
    class Meta:
        model = EmailTemplate
        fields = [
            'name', 'subject', 'template_type', 'status', 'html_content', 
            'text_content', 'variables', 'description', 'tags',
            'is_default', 'requires_approval'
        ]
    
    def validate_name(self, value):
        """Validate template name uniqueness"""
        if EmailTemplate.objects.filter(name=value, is_deleted=False).exists():
            raise serializers.ValidationError("Template with this name already exists.")
        return value
    
    def validate_variables(self, value):
        """Validate variables format"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Variables must be a dictionary.")
        return value


class EmailTemplateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating EmailTemplate"""
    
    class Meta:
        model = EmailTemplate
        fields = [
            'name', 'subject', 'template_type', 'status', 'html_content', 
            'text_content', 'variables', 'description', 'tags',
            'is_default', 'requires_approval'
        ]
    
    def validate_name(self, value):
        """Validate template name uniqueness (excluding current instance)"""
        if self.instance and EmailTemplate.objects.filter(name=value, is_deleted=False).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("Template with this name already exists.")
        return value


class EmailTemplatePreviewSerializer(serializers.Serializer):
    """Serializer for template preview"""
    context = serializers.JSONField(default=dict, help_text="Template variables for preview")
    
    def validate_context(self, value):
        """Validate context format"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Context must be a dictionary.")
        return value


class EmailTemplateTestSerializer(serializers.Serializer):
    """Serializer for template testing"""
    test_email = serializers.EmailField(help_text="Email address to send test to")
    context = serializers.JSONField(default=dict, help_text="Template variables for test")
    
    def validate_context(self, value):
        """Validate context format"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Context must be a dictionary.")
        return value


class EmailTemplateRenderSerializer(serializers.Serializer):
    """Serializer for template rendering"""
    context = serializers.JSONField(default=dict, help_text="Template variables")
    
    def validate_context(self, value):
        """Validate context format"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Context must be a dictionary.")
        return value


class EmailTemplateBulkActionSerializer(serializers.Serializer):
    """Serializer for bulk actions on templates"""
    template_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of template IDs"
    )
    action = serializers.ChoiceField(
        choices=[
            ('activate', 'Activate'),
            ('deactivate', 'Deactivate'),
            ('archive', 'Archive'),
            ('delete', 'Delete'),
        ],
        help_text="Action to perform"
    )
    
    def validate_template_ids(self, value):
        """Validate template IDs exist"""
        if not value:
            raise serializers.ValidationError("At least one template ID is required.")
        
        existing_ids = EmailTemplate.objects.filter(
            id__in=value, 
            is_deleted=False
        ).values_list('id', flat=True)
        
        if len(existing_ids) != len(value):
            missing_ids = set(value) - set(existing_ids)
            raise serializers.ValidationError(f"Templates with IDs {missing_ids} not found.")
        
        return value


class EmailTemplateStatisticsSerializer(serializers.Serializer):
    """Serializer for template statistics"""
    total_templates = serializers.IntegerField()
    active_templates = serializers.IntegerField()
    draft_templates = serializers.IntegerField()
    archived_templates = serializers.IntegerField()
    most_used_template = serializers.CharField()
    total_usage_count = serializers.IntegerField()
    templates_by_type = serializers.DictField()
    recent_templates = serializers.ListField()
