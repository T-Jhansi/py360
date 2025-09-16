from rest_framework import serializers
from .models import Template


class TemplateSerializer(serializers.ModelSerializer):
    """Serializer for Template model"""
    
    class Meta:
        model = Template
        fields = [
            'id',
            'name', 
            'template_type',
            'channel',
            'category',
            'subject',
            'content',
            'variables',
            'is_active',
            'created_by',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class TemplateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Template instances"""
    
    class Meta:
        model = Template
        fields = [
            'name',
            'template_type',
            'channel',
            'category',
            'subject',
            'content',
            'variables',
            'is_active'
        ]
    
    def validate_name(self, value):
        """Validate template name uniqueness"""
        if Template.objects.filter(name=value).exists():
            raise serializers.ValidationError("A template with this name already exists.")
        return value


class TemplateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating Template instances"""
    
    class Meta:
        model = Template
        fields = [
            'name',
            'template_type',
            'channel',
            'category',
            'subject',
            'content',
            'variables',
            'is_active'
        ]
    
    def validate_name(self, value):
        """Validate template name uniqueness (excluding current instance)"""
        if self.instance and Template.objects.filter(name=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("A template with this name already exists.")
        return value
