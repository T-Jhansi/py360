from rest_framework import serializers
from .models import PolicyCondition
from apps.policies.models import Policy


class FlexibleDescriptionField(serializers.Field):
    """Custom field that accepts both string and array formats for description"""

    def to_internal_value(self, data):
        """Convert input data to internal value"""
        # Handle array format (list of strings)
        if isinstance(data, list):
            if not data:
                raise serializers.ValidationError("Description cannot be empty.")

            # Filter out empty strings and strip whitespace
            cleaned_items = [item.strip() for item in data if isinstance(item, str) and item.strip()]

            if not cleaned_items:
                raise serializers.ValidationError("Description cannot be empty.")

            # Join array items with newlines to store as single text field
            return '\n'.join(cleaned_items)

        # Handle string format (backward compatibility)
        elif isinstance(data, str):
            if not data or not data.strip():
                raise serializers.ValidationError("Description cannot be empty.")
            return data.strip()

        else:
            raise serializers.ValidationError("Description must be a string or array of strings.")

    def to_representation(self, value):
        """Convert internal value to representation"""
        return value


class PolicyConditionSerializer(serializers.ModelSerializer):
    """Serializer for PolicyCondition model"""

    policy_id = serializers.IntegerField(write_only=True)
    policy_number = serializers.CharField(source='policy.policy_number', read_only=True)
    customer_name = serializers.CharField(source='policy.customer.full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)

    # Override description field to accept both string and array
    description = FlexibleDescriptionField()

    class Meta:
        model = PolicyCondition
        fields = [
            'id', 'policy_id', 'policy_number', 'customer_name', 'description',
            'created_by', 'created_by_name', 'updated_by', 'updated_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']
    
    def validate_policy_id(self, value):
        """Validate that the policy exists and is not deleted"""
        if not Policy.objects.filter(id=value, is_deleted=False).exists():
            raise serializers.ValidationError("Policy does not exist or has been deleted.")
        return value

    def create(self, validated_data):
        """Create policy condition with policy_id"""
        policy_id = validated_data.pop('policy_id')
        validated_data['policy_id'] = policy_id
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update policy condition with policy_id"""
        if 'policy_id' in validated_data:
            policy_id = validated_data.pop('policy_id')
            validated_data['policy_id'] = policy_id
        return super().update(instance, validated_data)
    



class PolicyConditionListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing policy conditions"""

    policy_number = serializers.CharField(source='policy.policy_number', read_only=True)
    customer_name = serializers.CharField(source='policy.customer.full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = PolicyCondition
        fields = [
            'id', 'policy_number', 'customer_name', 'description',
            'created_by_name', 'created_at'
        ]
