from rest_framework import serializers
from .models import PolicyExclusion
from apps.policies.models import Policy


class PolicyExclusionSerializer(serializers.ModelSerializer):
    """Serializer for PolicyExclusion model"""

    policy_number = serializers.CharField(source='policy.policy_number', read_only=True)
    policy_type_name = serializers.CharField(source='policy.policy_type.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)

    class Meta:
        model = PolicyExclusion
        fields = [
            'id', 'policy', 'policy_number', 'policy_type_name',
            'exclusion_type', 'description',
            'created_by', 'created_by_name', 'updated_by', 'updated_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PolicyExclusionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new policy exclusions"""

    # Accept policy_id instead of policy object
    policy_id = serializers.IntegerField(write_only=True)

    # Custom description field that accepts both string and array
    description = serializers.CharField(required=True)

    # Read-only fields for response
    policy_number = serializers.CharField(source='policy.policy_number', read_only=True)
    policy_type_name = serializers.CharField(source='policy.policy_type.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    exclusion_type_display = serializers.CharField(source='get_exclusion_type_display', read_only=True)

    class Meta:
        model = PolicyExclusion
        fields = [
            'id', 'policy_id', 'policy_number', 'policy_type_name',
            'exclusion_type', 'exclusion_type_display', 'description',
            'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def to_internal_value(self, data):
        """Handle both string and array formats for description"""
        # Make a copy of data to avoid modifying the original
        data = data.copy() if hasattr(data, 'copy') else dict(data)

        # Handle description field - convert array to string if needed
        if 'description' in data:
            description = data['description']
            if isinstance(description, list):
                # Convert array to string with bullet points
                data['description'] = '\n'.join([f"• {item}" for item in description])
            elif not isinstance(description, str):
                # Convert other types to string
                data['description'] = str(description)

        return super().to_internal_value(data)

    def validate_policy_id(self, value):
        """Ensure policy exists and is active"""
        if not Policy.objects.filter(id=value, is_deleted=False).exists():
            raise serializers.ValidationError("Policy does not exist or is deleted.")
        return value

    def create(self, validated_data):
        """Create policy exclusion"""
        policy_id = validated_data.pop('policy_id')

        # Get the policy object
        policy = Policy.objects.get(id=policy_id)
        validated_data['policy'] = policy

        return super().create(validated_data)


class PolicyExclusionUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating policy exclusions"""

    # Custom description field that accepts both string and array
    description = serializers.CharField(required=False)

    class Meta:
        model = PolicyExclusion
        fields = [
            'exclusion_type', 'description'
        ]

    def to_internal_value(self, data):
        """Handle both string and array formats for description"""
        # Make a copy of data to avoid modifying the original
        data = data.copy() if hasattr(data, 'copy') else dict(data)

        # Handle description field - convert array to string if needed
        if 'description' in data:
            description = data['description']
            if isinstance(description, list):
                # Convert array to string with bullet points
                data['description'] = '\n'.join([f"• {item}" for item in description])
            elif not isinstance(description, str):
                # Convert other types to string
                data['description'] = str(description)

        return super().to_internal_value(data)


class PolicyExclusionDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for frontend display"""

    policy_number = serializers.CharField(source='policy.policy_number', read_only=True)
    policy_type_name = serializers.CharField(source='policy.policy_type.name', read_only=True)
    exclusion_type_display = serializers.CharField(source='get_exclusion_type_display', read_only=True)

    class Meta:
        model = PolicyExclusion
        fields = [
            'id', 'policy_number', 'policy_type_name',
            'exclusion_type', 'exclusion_type_display', 'description',
            'created_at', 'updated_at'
        ]
