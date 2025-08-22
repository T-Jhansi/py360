from rest_framework import serializers
from .models import PolicyAdditionalBenefit
from apps.policy_coverages.models import PolicyCoverage


class PolicyAdditionalBenefitSerializer(serializers.ModelSerializer):
    """Serializer for PolicyAdditionalBenefit model"""

    policy_coverages_id = serializers.IntegerField(write_only=True)
    policy_type_name = serializers.CharField(source='policy_coverages.policy_type.name', read_only=True)
    coverage_name = serializers.CharField(source='policy_coverages.coverage_name', read_only=True)
    coverage_type = serializers.CharField(source='policy_coverages.coverage_type', read_only=True)

    class Meta:
        model = PolicyAdditionalBenefit
        fields = [
            'id', 'policy_coverages_id', 'policy_type_name', 'coverage_name', 'coverage_type',
            'benefit_category', 'benefit_type', 'benefit_name', 'benefit_description', 'benefit_value',
            'coverage_amount', 'is_active', 'is_optional', 'premium_impact',
            'display_order', 'terms_conditions', 'additional_info',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_policy_coverages_id(self, value):
        """Validate that the policy coverage exists and is active"""
        if not PolicyCoverage.objects.filter(id=value, is_deleted=False).exists():
            raise serializers.ValidationError("Policy coverage does not exist or has been deleted.")
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

    policy_type_name = serializers.CharField(source='policy_coverages.policy_type.name', read_only=True)
    coverage_name = serializers.CharField(source='policy_coverages.coverage_name', read_only=True)

    class Meta:
        model = PolicyAdditionalBenefit
        fields = [
            'id', 'policy_type_name', 'coverage_name', 'benefit_category', 'benefit_type',
            'benefit_name', 'benefit_description', 'coverage_amount',
            'is_active', 'is_optional', 'premium_impact', 'created_at'
        ]


class PolicyAdditionalBenefitStoreSerializer(serializers.ModelSerializer):
    """Serializer for storing policy additional benefits based on the image structure"""

    policy_coverage_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = PolicyAdditionalBenefit
        fields = [
            'policy_coverage_id', 'benefit_category', 'benefit_name', 'benefit_value',
            'benefit_description', 'coverage_amount', 'is_active', 'is_optional',
            'premium_impact', 'display_order', 'terms_conditions'
        ]

    def validate_policy_coverage_id(self, value):
        """Validate that the policy coverage exists"""
        from apps.policy_coverages.models import PolicyCoverage
        if not PolicyCoverage.objects.filter(id=value, is_deleted=False).exists():
            raise serializers.ValidationError("Policy coverage does not exist or has been deleted.")
        return value

    def validate_benefit_name(self, value):
        """Validate benefit name is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Benefit name cannot be empty.")
        return value.strip()

    def validate_benefit_category(self, value):
        """Validate benefit category is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Benefit category cannot be empty.")
        return value.strip()

    def create(self, validated_data):
        """Create policy additional benefit with policy_coverages relationship"""
        policy_coverage_id = validated_data.pop('policy_coverage_id')
        from apps.policy_coverages.models import PolicyCoverage
        policy_coverage = PolicyCoverage.objects.get(id=policy_coverage_id)

        benefit = PolicyAdditionalBenefit.objects.create(
            policy_coverages=policy_coverage,
            **validated_data
        )
        return benefit


class PolicyAdditionalBenefitDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for listing policy additional benefits based on image structure"""

    policy_coverage_id = serializers.IntegerField(source='policy_coverages.id', read_only=True)
    policy_type_name = serializers.CharField(source='policy_coverages.policy_type.name', read_only=True)
    coverage_name = serializers.CharField(source='policy_coverages.coverage_name', read_only=True)

    class Meta:
        model = PolicyAdditionalBenefit
        fields = [
            'id', 'policy_coverage_id', 'policy_type_name', 'coverage_name',
            'benefit_category', 'benefit_name', 'benefit_value', 'benefit_description',
            'coverage_amount', 'is_active', 'is_optional', 'premium_impact',
            'display_order', 'created_at', 'updated_at'
        ]
