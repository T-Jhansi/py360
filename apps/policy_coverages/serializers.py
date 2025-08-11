from rest_framework import serializers
from .models import PolicyCoverage
from apps.policies.models import Policy


class PolicyCoverageSerializer(serializers.ModelSerializer):
    """Serializer for PolicyCoverage model"""
    
    policy_number = serializers.CharField(source='policy.policy_number', read_only=True)
    customer_name = serializers.CharField(source='policy.customer.name', read_only=True)
    policy_type_name = serializers.CharField(source='policy.policy_type.name', read_only=True)
    
    class Meta:
        model = PolicyCoverage
        fields = [
            'id', 'policy', 'policy_number', 'customer_name', 'policy_type_name',
            'coverage_type', 'coverage_category', 'coverage_name', 'coverage_description',
            'coverage_amount', 'deductible_amount', 'coverage_percentage',
            'is_included', 'is_optional', 'premium_impact', 'display_order',
            'terms_conditions', 'exclusions', 'additional_info',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_policy(self, value):
        """Validate that the policy exists and is active"""
        if not Policy.objects.filter(id=value.id, is_deleted=False).exists():
            raise serializers.ValidationError("Policy does not exist or has been deleted.")
        return value
    
    def validate_coverage_name(self, value):
        """Validate coverage name is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Coverage name cannot be empty.")
        return value.strip()
    
    def validate_coverage_description(self, value):
        """Validate coverage description is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Coverage description cannot be empty.")
        return value.strip()
    
    def validate_coverage_amount(self, value):
        """Validate coverage amount is positive if provided"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Coverage amount cannot be negative.")
        return value
    
    def validate_deductible_amount(self, value):
        """Validate deductible amount is positive if provided"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Deductible amount cannot be negative.")
        return value
    
    def validate_coverage_percentage(self, value):
        """Validate coverage percentage is between 0 and 100"""
        if value is not None and (value < 0 or value > 100):
            raise serializers.ValidationError("Coverage percentage must be between 0 and 100.")
        return value
    
    def validate_premium_impact(self, value):
        """Validate premium impact is not negative"""
        if value < 0:
            raise serializers.ValidationError("Premium impact cannot be negative.")
        return value


class PolicyCoverageListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing policy coverages"""
    
    policy_number = serializers.CharField(source='policy.policy_number', read_only=True)
    customer_name = serializers.CharField(source='policy.customer.name', read_only=True)
    
    class Meta:
        model = PolicyCoverage
        fields = [
            'id', 'policy_number', 'customer_name', 'coverage_type', 
            'coverage_category', 'coverage_name', 'coverage_description',
            'coverage_amount', 'deductible_amount', 'coverage_percentage',
            'is_included', 'is_optional', 'premium_impact', 'created_at'
        ]


class PolicyCoverageSummarySerializer(serializers.ModelSerializer):
    """Summary serializer for coverage overview"""
    
    class Meta:
        model = PolicyCoverage
        fields = [
            'id', 'coverage_type', 'coverage_name', 'coverage_amount',
            'deductible_amount', 'coverage_percentage', 'is_included'
        ]
