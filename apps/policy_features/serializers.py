from rest_framework import serializers
from .models import PolicyFeature
from apps.policies.models import PolicyType


class PolicyFeatureSerializer(serializers.ModelSerializer):
    """Serializer for PolicyFeature model"""

    policy_type_name = serializers.CharField(source='policy_type.name', read_only=True)
    policy_type_code = serializers.CharField(source='policy_type.code', read_only=True)
    policy_type_category = serializers.CharField(source='policy_type.category', read_only=True)

    class Meta:
        model = PolicyFeature
        fields = [
            'id', 'policy_type', 'policy_type_name', 'policy_type_code', 'policy_type_category',
            'feature_type', 'feature_name', 'feature_description', 'feature_value',
            'is_active', 'is_mandatory', 'display_order', 'additional_info',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_policy_type(self, value):
        """Validate that the policy type exists and is active"""
        if not PolicyType.objects.filter(id=value.id, is_deleted=False).exists():
            raise serializers.ValidationError("Policy type does not exist or has been deleted.")
        return value
    
    def validate_feature_name(self, value):
        """Validate feature name is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Feature name cannot be empty.")
        return value.strip()
    
    def validate_feature_description(self, value):
        """Validate feature description is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Feature description cannot be empty.")
        return value.strip()


class PolicyFeatureListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing policy features"""

    policy_type_name = serializers.CharField(source='policy_type.name', read_only=True)
    policy_type_code = serializers.CharField(source='policy_type.code', read_only=True)

    class Meta:
        model = PolicyFeature
        fields = [
            'id', 'policy_type_name', 'policy_type_code', 'feature_type',
            'feature_name', 'feature_description', 'is_active',
            'is_mandatory', 'created_at'
        ]
