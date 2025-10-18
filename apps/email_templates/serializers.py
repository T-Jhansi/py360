from rest_framework import serializers
from .models import EmailTemplate, EmailTemplateCategory, EmailTemplateTag, EmailTemplateVersion


class EmailTemplateCategorySerializer(serializers.ModelSerializer):
    """Serializer for EmailTemplateCategory"""
    template_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = EmailTemplateCategory
        fields = ['id', 'name', 'description', 'color', 'is_active', 'template_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class EmailTemplateTagSerializer(serializers.ModelSerializer):
    """Serializer for EmailTemplateTag"""
    template_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = EmailTemplateTag
        fields = ['id', 'name', 'description', 'color', 'is_active', 'template_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class EmailTemplateWriteSerializerBase(serializers.ModelSerializer):
    """Base serializer for handling write operations for templates."""
    tags = serializers.PrimaryKeyRelatedField(
        queryset=EmailTemplateTag.objects.filter(is_active=True, is_deleted=False),
        many=True, required=False
    )
    category = serializers.PrimaryKeyRelatedField(
        queryset=EmailTemplateCategory.objects.filter(is_active=True, is_deleted=False),
        required=False, allow_null=True
    )

    class Meta:
        model = EmailTemplate
        fields = [
            'name', 'subject', 'description', 'html_content', 'text_content',
            'template_type', 'variables', 'category', 'tags', 'status', 'is_public'
        ]


class EmailTemplateCreateSerializer(EmailTemplateWriteSerializerBase):
    """Serializer for creating EmailTemplate."""
    pass


class EmailTemplateUpdateSerializer(EmailTemplateWriteSerializerBase):
    """Serializer for updating EmailTemplate."""
    pass


class EmailTemplateSerializer(serializers.ModelSerializer):
    """Main serializer for displaying EmailTemplate data."""
    category = EmailTemplateCategorySerializer(read_only=True)
    tags = EmailTemplateTagSerializer(many=True, read_only=True)
    
    # _# FIXED:_ Using SerializerMethodField for safety against NULL values.
    created_by_name = serializers.SerializerMethodField()
    updated_by_name = serializers.SerializerMethodField()

    class Meta:
        model = EmailTemplate
        fields = [
            'id', 'name', 'subject', 'description', 'html_content', 'text_content',
            'template_type', 'variables', 'category', 'tags', 'status',
            'is_public', 'usage_count', 'last_used', 'created_at', 'updated_at',
            'created_by_name', 'updated_by_name'
        ]
        read_only_fields = fields

    def get_created_by_name(self, obj):
        """Safely get the full name of the creator, or None if not available."""
        if obj.created_by:
            return obj.created_by.get_full_name()
        return None

    def get_updated_by_name(self, obj):
        """Safely get the full name of the updater, or None if not available."""
        if obj.updated_by:
            return obj.updated_by.get_full_name()
        return None


class EmailTemplateVersionSerializer(serializers.ModelSerializer):
    """Serializer for EmailTemplateVersion"""
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = EmailTemplateVersion
        fields = [
            'id', 'template', 'version_number', 'name', 'subject',
            'html_content', 'text_content', 'change_summary', 'created_at', 'created_by_name'
        ]
        read_only_fields = fields

    def get_created_by_name(self, obj):
        """Safely get the full name of the creator."""
        if obj.created_by:
            return obj.created_by.get_full_name()
        return None


class EmailTemplateRenderSerializer(serializers.Serializer):
    """Serializer for validating the context for rendering an email."""
    context = serializers.DictField(
        child=serializers.CharField(allow_blank=True),
        required=True,
        help_text="Context variables for template rendering"
    )