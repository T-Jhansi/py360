from rest_framework import serializers
from .models import RenewalTimeline


class RenewalTimelineListSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    policy_number = serializers.CharField(source='policy.policy_number', read_only=True)
    preferred_channel_name = serializers.CharField(source='preferred_channel.name', read_only=True)

    class Meta:
        model = RenewalTimeline
        fields = [
            'id',
            'customer',
            'customer_name',
            'policy',
            'policy_number',
            'renewal_case',
            'preferred_channel',
            'preferred_channel_name',
            'renewal_pattern',
            'reminder_days',
            'next_due_date',
            'auto_renewal_enabled',
            'is_active',
            'created_at',
            'updated_at',
        ]


class RenewalTimelineDetailSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    policy_number = serializers.CharField(source='policy.policy_number', read_only=True)
    preferred_channel_name = serializers.CharField(source='preferred_channel.name', read_only=True)

    class Meta:
        model = RenewalTimeline
        fields = [
            'id',
            'customer',
            'customer_name',
            'policy',
            'policy_number',
            'renewal_case',
            'preferred_channel',
            'preferred_channel_name',
            'last_payment',
            'renewal_pattern',
            'reminder_days',
            'next_due_date',
            'auto_renewal_enabled',
            'is_active',
            'notes',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by',
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


class RenewalTimelineCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RenewalTimeline
        fields = [
            'customer',
            'policy',
            'renewal_case',
            'preferred_channel',
            'last_payment',
            'renewal_pattern',
            'reminder_days',
            'next_due_date',
            'auto_renewal_enabled',
            'is_active',
            'notes',
        ]

    # Creation handled in ViewSet.perform_create to avoid direct manager typing issues


