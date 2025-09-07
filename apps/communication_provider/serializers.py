from rest_framework import serializers
from .models import CommunicationProvider


class CommunicationProviderSerializer(serializers.ModelSerializer):    
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.full_name', read_only=True)
    deleted_by_name = serializers.CharField(source='deleted_by.full_name', read_only=True)
    channel_display = serializers.CharField(source='get_channel_display', read_only=True)
    is_deleted = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = CommunicationProvider
        fields = [
            'id',
            'name',
            'channel',
            'channel_display',
            'is_default',
            'is_active',
            'created_by',
            'created_by_name',
            'updated_by',
            'updated_by_name',
            'deleted_by',
            'deleted_by_name',
            'created_at',
            'updated_at',
            'deleted_at',
            'is_deleted'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'deleted_at', 'is_deleted']

    def validate(self, data):
        """Custom validation"""
        if data.get('is_default', False):
            channel = data.get('channel')
            if channel:
                existing_default = CommunicationProvider.objects.filter(
                    channel=channel,
                    is_default=True,
                    is_deleted=False
                ).exclude(pk=self.instance.pk if self.instance else None)
                
                if existing_default.exists():
                    raise serializers.ValidationError({
                        'is_default': f'There is already a default provider for {channel} channel.'
                    })
        
        return data

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Override update to set updated_by"""
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class CommunicationProviderListSerializer(serializers.ModelSerializer):    
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    channel_display = serializers.CharField(source='get_channel_display', read_only=True)
    
    class Meta:
        model = CommunicationProvider
        fields = [
            'id',
            'name',
            'channel',
            'channel_display',
            'is_default',
            'is_active',
            'created_by_name',
            'created_at'
        ]


class CommunicationProviderCreateSerializer(serializers.ModelSerializer):    
    class Meta:
        model = CommunicationProvider
        fields = [
            'name',
            'channel',
            'is_default',
            'is_active'
        ]

    def validate(self, data):
        if data.get('is_default', False):
            channel = data.get('channel')
            if channel:
                existing_default = CommunicationProvider.objects.filter(
                    channel=channel,
                    is_default=True,
                    is_deleted=False
                )
                
                if existing_default.exists():
                    raise serializers.ValidationError({
                        'is_default': f'There is already a default provider for {channel} channel.'
                    })
        
        return data

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
