from rest_framework import serializers
from .models import EmailTemplate, EmailTemplateCategory, EmailTemplateTag, EmailTemplateVersion


class EmailTemplateCategorySerializer(serializers.ModelSerializer):
    """Serializer for EmailTemplateCategory"""
    
    template_count = serializers.SerializerMethodField()
    
    class Meta:
        model = EmailTemplateCategory
        fields = [
            'id', 'name', 'description', 'color', 'is_active',
            'template_count', 'created_at', 'updated_at', 'created_by',
            'updated_by', 'is_deleted', 'deleted_at', 'deleted_by'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'created_by', 'updated_by',
            'is_deleted', 'deleted_at', 'deleted_by'
        ]
    
    def get_template_count(self, obj):
        """Get count of templates in this category"""
        return obj.templates.filter(is_deleted=False).count()
    
    def create(self, validated_data):
        """Set created_by when creating a new category"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Set updated_by when updating a category"""
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class EmailTemplateTagSerializer(serializers.ModelSerializer):
    """Serializer for EmailTemplateTag"""
    
    template_count = serializers.SerializerMethodField()
    
    class Meta:
        model = EmailTemplateTag
        fields = [
            'id', 'name', 'description', 'color', 'is_active',
            'template_count', 'created_at', 'updated_at', 'created_by',
            'updated_by', 'is_deleted', 'deleted_at', 'deleted_by'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'created_by', 'updated_by',
            'is_deleted', 'deleted_at', 'deleted_by'
        ]
    
    def get_template_count(self, obj):
        """Get count of templates with this tag"""
        return obj.templates.filter(is_deleted=False).count()
    
    def create(self, validated_data):
        """Set created_by when creating a new tag"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Set updated_by when updating a tag"""
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class EmailTemplateSerializer(serializers.ModelSerializer):
    """Serializer for EmailTemplate"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)
    tags_data = EmailTemplateTagSerializer(source='tags', many=True, read_only=True)
    tag_names = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False,
        help_text="List of tag names to assign to this template"
    )
    template_type_display = serializers.CharField(source='get_template_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)
    
    class Meta:
        model = EmailTemplate
        fields = [
            'id', 'name', 'subject', 'description', 'html_content', 'text_content',
            'template_type', 'template_type_display', 'variables', 'category',
            'category_name', 'category_color', 'tags', 'tags_data', 'tag_names',
            'status', 'status_display', 'is_default', 'is_public', 'usage_count',
            'last_used', 'created_at', 'updated_at', 'created_by', 'created_by_name',
            'updated_by', 'updated_by_name', 'is_deleted', 'deleted_at', 'deleted_by'
        ]
        read_only_fields = [
            'id', 'usage_count', 'last_used', 'created_at', 'updated_at',
            'created_by', 'updated_by', 'is_deleted', 'deleted_at', 'deleted_by'
        ]
    
    def create(self, validated_data):
        """Create a new email template"""
        tag_names = validated_data.pop('tag_names', [])
        validated_data['created_by'] = self.context['request'].user
        
        template = super().create(validated_data)
        
        # Assign tags
        if tag_names:
            tags = EmailTemplateTag.objects.filter(name__in=tag_names, is_deleted=False)
            template.tags.set(tags)
        
        # Create initial version
        EmailTemplateVersion.objects.create(
            template=template,
            name=template.name,
            subject=template.subject,
            html_content=template.html_content,
            text_content=template.text_content,
            template_type=template.template_type,
            variables=template.variables,
            is_current=True,
            created_by=self.context['request'].user
        )
        
        return template
    
    def update(self, instance, validated_data):
        """Update an email template"""
        tag_names = validated_data.pop('tag_names', None)
        validated_data['updated_by'] = self.context['request'].user
        
        # Create new version if content changed
        content_changed = any(field in validated_data for field in [
            'name', 'subject', 'html_content', 'text_content', 'template_type', 'variables'
        ])
        
        if content_changed:
            # Create new version
            EmailTemplateVersion.objects.create(
                template=instance,
                name=instance.name,
                subject=instance.subject,
                html_content=instance.html_content,
                text_content=instance.text_content,
                template_type=instance.template_type,
                variables=instance.variables,
                change_summary=f"Updated by {self.context['request'].user.get_full_name()}",
                created_by=self.context['request'].user
            )
        
        template = super().update(instance, validated_data)
        
        # Update tags if provided
        if tag_names is not None:
            tags = EmailTemplateTag.objects.filter(name__in=tag_names, is_deleted=False)
            template.tags.set(tags)
        
        return template


class EmailTemplateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating EmailTemplate (simplified)"""
    
    tag_names = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="List of tag names to assign to this template"
    )
    
    class Meta:
        model = EmailTemplate
        fields = [
            'name', 'subject', 'description', 'html_content', 'text_content',
            'template_type', 'variables', 'category', 'tag_names', 'status',
            'is_default', 'is_public'
        ]
    
    def create(self, validated_data):
        """Create a new email template"""
        tag_names = validated_data.pop('tag_names', [])
        validated_data['created_by'] = self.context['request'].user
        
        template = super().create(validated_data)
        
        # Assign tags
        if tag_names:
            tags = EmailTemplateTag.objects.filter(name__in=tag_names, is_deleted=False)
            template.tags.set(tags)
        
        # Create initial version
        EmailTemplateVersion.objects.create(
            template=template,
            name=template.name,
            subject=template.subject,
            html_content=template.html_content,
            text_content=template.text_content,
            template_type=template.template_type,
            variables=template.variables,
            is_current=True,
            created_by=self.context['request'].user
        )
        
        return template


class EmailTemplateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating EmailTemplate"""
    
    tag_names = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="List of tag names to assign to this template"
    )
    
    class Meta:
        model = EmailTemplate
        fields = [
            'name', 'subject', 'description', 'html_content', 'text_content',
            'template_type', 'variables', 'category', 'tag_names', 'status',
            'is_default', 'is_public'
        ]
    
    def update(self, instance, validated_data):
        """Update an email template"""
        tag_names = validated_data.pop('tag_names', None)
        validated_data['updated_by'] = self.context['request'].user
        
        # Create new version if content changed
        content_changed = any(field in validated_data for field in [
            'name', 'subject', 'html_content', 'text_content', 'template_type', 'variables'
        ])
        
        if content_changed:
            # Create new version
            EmailTemplateVersion.objects.create(
                template=instance,
                name=instance.name,
                subject=instance.subject,
                html_content=instance.html_content,
                text_content=instance.text_content,
                template_type=instance.template_type,
                variables=instance.variables,
                change_summary=f"Updated by {self.context['request'].user.get_full_name()}",
                created_by=self.context['request'].user
            )
        
        template = super().update(instance, validated_data)
        
        # Update tags if provided
        if tag_names is not None:
            tags = EmailTemplateTag.objects.filter(name__in=tag_names, is_deleted=False)
            template.tags.set(tags)
        
        return template


class EmailTemplateVersionSerializer(serializers.ModelSerializer):
    """Serializer for EmailTemplateVersion"""
    
    template_name = serializers.CharField(source='template.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    template_type_display = serializers.CharField(source='get_template_type_display', read_only=True)
    
    class Meta:
        model = EmailTemplateVersion
        fields = [
            'id', 'template', 'template_name', 'version_number', 'name', 'subject',
            'html_content', 'text_content', 'template_type', 'template_type_display',
            'variables', 'change_summary', 'is_current', 'created_at', 'created_by',
            'created_by_name'
        ]
        read_only_fields = ['id', 'version_number', 'created_at', 'created_by']


class EmailTemplateRenderSerializer(serializers.Serializer):
    """Serializer for rendering email templates with context"""
    
    template_id = serializers.UUIDField()
    context = serializers.DictField(
        child=serializers.CharField(),
        required=False,
        default=dict,
        help_text="Context variables for template rendering"
    )
    
    def validate_template_id(self, value):
        """Validate that template exists and is active"""
        try:
            template = EmailTemplate.objects.get(id=value, is_deleted=False)
            if template.status != 'active':
                raise serializers.ValidationError("Template is not active")
            return value
        except EmailTemplate.DoesNotExist:
            raise serializers.ValidationError("Template not found")


class EmailTemplateStatsSerializer(serializers.Serializer):
    """Serializer for email template statistics"""
    
    template_id = serializers.UUIDField()
    template_name = serializers.CharField()
    category_name = serializers.CharField()
    status = serializers.CharField()
    usage_count = serializers.IntegerField()
    last_used = serializers.DateTimeField()
    created_at = serializers.DateTimeField()
    created_by_name = serializers.CharField()
    version_count = serializers.IntegerField()
    tag_count = serializers.IntegerField()
