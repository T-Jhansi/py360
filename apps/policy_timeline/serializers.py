"""
Policy Timeline serializers for the Intelipro Insurance Policy Renewal System.
"""

from rest_framework import serializers
from .models import PolicyTimeline
from apps.customers.serializers import CustomerSerializer
from apps.policies.serializers import PolicySerializer
from apps.users.serializers import UserSerializer


class PolicyTimelineSerializer(serializers.ModelSerializer):
    """Serializer for Policy Timeline model"""
    
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    policy_number = serializers.CharField(source='policy.policy_number', read_only=True)
    agent_name = serializers.CharField(source='agent.get_full_name', read_only=True)
    formatted_event_date = serializers.CharField(read_only=True)
    event_category_display = serializers.CharField(read_only=True)
    
    class Meta:
        model = PolicyTimeline
        fields = [
            'id',
            'policy',
            'customer',
            'agent',
            'event_type',
            'event_title',
            'event_description',
            'event_date',
            'event_status',
            'premium_amount',
            'coverage_details',
            'discount_info',
            'outcome',
            'follow_up_required',
            'follow_up_date',
            'display_icon',
            'is_milestone',
            'sequence_order',
            'created_at',
            'updated_at',
            # Read-only fields
            'customer_name',
            'policy_number',
            'agent_name',
            'formatted_event_date',
            'event_category_display',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'customer_name',
            'policy_number',
            'agent_name',
            'formatted_event_date',
            'event_category_display',
        ]


class PolicyTimelineDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Policy Timeline with related objects"""
    
    customer = CustomerSerializer(read_only=True)
    policy = PolicySerializer(read_only=True)
    agent = UserSerializer(read_only=True)
    formatted_event_date = serializers.CharField(read_only=True)
    event_category_display = serializers.CharField(read_only=True)
    
    class Meta:
        model = PolicyTimeline
        fields = [
            'id',
            'policy',
            'customer',
            'agent',
            'event_type',
            'event_title',
            'event_description',
            'event_date',
            'event_status',
            'premium_amount',
            'coverage_details',
            'discount_info',
            'outcome',
            'follow_up_required',
            'follow_up_date',
            'display_icon',
            'is_milestone',
            'sequence_order',
            'created_at',
            'updated_at',
            'formatted_event_date',
            'event_category_display',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'formatted_event_date',
            'event_category_display',
        ]


class PolicyTimelineCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Policy Timeline events"""
    
    class Meta:
        model = PolicyTimeline
        fields = [
            'policy',
            'customer',
            'agent',
            'event_type',
            'event_title',
            'event_description',
            'event_date',
            'event_status',
            'premium_amount',
            'coverage_details',
            'discount_info',
            'outcome',
            'follow_up_required',
            'follow_up_date',
            'display_icon',
            'is_milestone',
            'sequence_order',
        ]
    
    def validate(self, data):
        """Validate the timeline event data"""
        # Ensure customer matches the policy's customer
        if data.get('policy') and data.get('customer'):
            if data['policy'].customer != data['customer']:
                raise serializers.ValidationError(
                    "Customer must match the policy's customer"
                )
        
        # Ensure follow_up_date is provided if follow_up_required is True
        if data.get('follow_up_required') and not data.get('follow_up_date'):
            raise serializers.ValidationError(
                "Follow-up date is required when follow-up is marked as required"
            )
        
        return data
