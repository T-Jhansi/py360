from rest_framework import serializers
from .models import PolicyAdditionalBenefit
from apps.policies.models import Policy


class PolicyAdditionalBenefitSerializer(serializers.ModelSerializer):
    """Serializer for PolicyAdditionalBenefit model"""
    
    policy_number = serializers.CharField(source='policy.policy_number', read_only=True)
    customer_name = serializers.CharField(source='policy.customer.name', read_only=True)
    policy_type_name = serializers.CharField(source='policy.policy_type.name', read_only=True)
    
    class Meta:
        model = PolicyAdditionalBenefit
        fields = [
            'id', 'policy', 'policy_number', 'customer_name', 'policy_type_name',
            'benefit_type', 'benefit_name', 'benefit_description', 'benefit_value',
            'coverage_amount', 'is_active', 'is_optional', 'premium_impact',
            'display_order', 'terms_conditions', 'additional_info',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_policy(self, value):
        """Validate that the policy exists and is active"""
        if not Policy.objects.filter(id=value.id, is_deleted=False).exists():
            raise serializers.ValidationError("Policy does not exist or has been deleted.")
        return value
    
    def validate_benefit_name(self, value):
        """Validate benefit name is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Benefit name cannot be empty.")
        return value.strip()
    
    def validate_benefit_description(self, value):
        """Validate benefit description is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Benefit description cannot be empty.")
        return value.strip()
    
    def validate_coverage_amount(self, value):
        """Validate coverage amount is positive if provided"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Coverage amount cannot be negative.")
        return value
    
    def validate_premium_impact(self, value):
        """Validate premium impact is not negative"""
        if value < 0:
            raise serializers.ValidationError("Premium impact cannot be negative.")
        return value


class PolicyAdditionalBenefitListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing policy additional benefits"""
    
    policy_number = serializers.CharField(source='policy.policy_number', read_only=True)
    customer_name = serializers.CharField(source='policy.customer.name', read_only=True)
    
    class Meta:
        model = PolicyAdditionalBenefit
        fields = [
            'id', 'policy_number', 'customer_name', 'benefit_type', 
            'benefit_name', 'benefit_description', 'coverage_amount',
            'is_active', 'is_optional', 'premium_impact', 'created_at'
        ]
