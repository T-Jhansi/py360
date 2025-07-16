from rest_framework import serializers
from .models import Campaign

class CampaignSerializer(serializers.ModelSerializer):
    # created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    # assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)

    class Meta:
        model = Campaign
        fields = [
            'id', 'name', 'campaign_type', 'description', 'status',
            'target_count','upload', 'delivered_count', 'sent_count', 'opened_count', 'clicked_count', 'total_responses',
            'channels', 'target_audience', 'started_at', 'completed_at',
            'is_recurring', 'recurrence_pattern', 'subject_line',
            'template', 'use_personalization', 'personalization_fields',
            'created_by', 'assigned_to','created_at', 'updated_at','delivery_rate', 'open_rate', 'click_rate', 'response_rate',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'delivery_rate', 'open_rate', 'click_rate', 'response_rate', 'created_by']
