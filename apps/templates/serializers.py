from rest_framework import serializers
from .models import Template


class TemplateSerializer(serializers.ModelSerializer):
    """Serializer for Template model"""
    
    class Meta:
        model = Template
        fields = [
            'id',
            'name', 
            'channel',
            'subject',
            'content',
            'variables',
            'is_active',
            'created_by',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
