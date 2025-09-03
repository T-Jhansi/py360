from rest_framework import serializers
from .models import RenewalTimeline
from typing import Any  # for type: ignore hints
from apps.customers.models import Customer
from apps.policies.models import Policy
from apps.channels.models import Channel
from apps.renewals.models import RenewalCase
from apps.customer_payments.models import CustomerPayment


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
    # Accept *_id aliases for FKs
    customer_id = serializers.PrimaryKeyRelatedField(
        source='customer', queryset=Customer.objects.all(), write_only=True  # type: ignore[attr-defined]
    )
    policy_id = serializers.PrimaryKeyRelatedField(
        source='policy', queryset=Policy.objects.all(), write_only=True  # type: ignore[attr-defined]
    )
    renewal_case_id = serializers.PrimaryKeyRelatedField(
        source='renewal_case', queryset=RenewalCase.objects.all(), required=False, allow_null=True, write_only=True  # type: ignore[attr-defined]
    )
    preferred_channel_id = serializers.PrimaryKeyRelatedField(
        source='preferred_channel', queryset=Channel.objects.all(), required=False, allow_null=True, write_only=True  # type: ignore[attr-defined]
    )
    last_payment_id = serializers.PrimaryKeyRelatedField(
        source='last_payment', queryset=CustomerPayment.objects.all(), required=False, allow_null=True, write_only=True  # type: ignore[attr-defined]
    )
    class Meta:
        model = RenewalTimeline
        fields = [
            'customer_id',
            'policy_id',
            'renewal_case_id',
            'preferred_channel_id',
            'last_payment_id',
            'renewal_pattern',
            'reminder_days',
            'next_due_date',
            'auto_renewal_enabled',
            'is_active',
            'notes',
        ]
        extra_kwargs = {}

    # Creation handled in ViewSet.perform_create to avoid direct manager typing issues


