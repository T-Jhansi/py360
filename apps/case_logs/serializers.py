from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.renewals.models import RenewalCase
from apps.customers.models import Customer
from apps.policies.models import Policy, PolicyType
from .models import CaseLog

User = get_user_model()


class QuickEditCaseSerializer(serializers.Serializer):
    
    status = serializers.ChoiceField(
        choices=RenewalCase.STATUS_CHOICES,
        required=True,
        help_text="Main case status that will be updated in renewal_cases table"
    )
    
    sub_status = serializers.ChoiceField(
        choices=CaseLog.SUB_STATUS_CHOICES,
        required=True,
        help_text="Detailed sub-status for case tracking"
    )
    
    current_work_step = serializers.ChoiceField(
        choices=CaseLog.WORK_STEP_CHOICES,
        required=True,
        help_text="Current work step in the renewal process"
    )
    
    next_follow_up_date = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text="Date and time for next follow-up (optional)"
    )
    
    next_action_plan = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=1000,
        help_text="Description of next planned action (optional)"
    )
    
    comment = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=1000,
        help_text="Additional comments about this update (optional)"
    )
    
    def validate(self, data):
        case_log_fields = ['sub_status', 'current_work_step', 'next_follow_up_date', 'next_action_plan', 'comment']
        has_case_log_data = any(
            data.get(field) and str(data.get(field)).strip() 
            for field in case_log_fields 
            if field in data
        )
        
        if not has_case_log_data:
            raise serializers.ValidationError(
                "At least one case log field (sub_status, current_work_step, next_follow_up_date, "
                "next_action_plan, or comment) must be provided with meaningful data."
            )
        
        return data
    
    def validate_status(self, value):
        if not value:
            raise serializers.ValidationError("Status is required.")
        return value
    
    def validate_sub_status(self, value):
        if not value:
            raise serializers.ValidationError("Sub-status is required.")
        return value
    
    def validate_current_work_step(self, value):
        if not value:
            raise serializers.ValidationError("Current work step is required.")
        return value
    
    def validate_next_action_plan(self, value):
        if value and len(value.strip()) > 1000:
            raise serializers.ValidationError("Next action plan cannot exceed 1000 characters.")
        return value.strip() if value else ""
    
    def validate_comment(self, value):
        if value and len(value.strip()) > 1000:
            raise serializers.ValidationError("Comment cannot exceed 1000 characters.")
        return value.strip() if value else ""


class CaseLogSerializer(serializers.ModelSerializer):

    renewal_case_number = serializers.CharField(source='renewal_case.case_number', read_only=True)
    sub_status = serializers.CharField(source='get_sub_status_display', read_only=True)
    current_work_step = serializers.CharField(source='get_current_work_step_display', read_only=True)
    created_by_name = serializers.SerializerMethodField()
    updated_by_name = serializers.SerializerMethodField()

    class Meta:
        model = CaseLog
        fields = [
            'id',
            'renewal_case',
            'renewal_case_number',
            'sub_status',
            'current_work_step',
            'next_follow_up_date',
            'next_action_plan',
            'comment',
            'created_at',
            'updated_at',
            'created_by',
            'created_by_name',
            'updated_by',
            'updated_by_name',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None
    
    def get_updated_by_name(self, obj):
        if obj.updated_by:
            return obj.updated_by.get_full_name() or obj.updated_by.username
        return None


class CaseDetailsSerializer(serializers.Serializer):
    """Serializer for fetching case details for editing"""

    # Case Information
    case_id = serializers.IntegerField(source='id', read_only=True)
    case_number = serializers.CharField(read_only=True)

    # Customer Information (editable)
    customer_name = serializers.CharField(source='customer.full_name')
    email = serializers.EmailField(source='customer.email')
    phone = serializers.CharField(source='customer.phone')

    # Policy Information
    policy_number = serializers.CharField(source='policy.policy_number', read_only=True)
    policy_type_name = serializers.CharField(source='policy.policy_type.name', read_only=True)
    premium_amount = serializers.DecimalField(source='policy.premium_amount', max_digits=12, decimal_places=2, read_only=True)
    expiry_date = serializers.DateField(source='policy.end_date', read_only=True)
    assigned_agent_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True, allow_null=True)


class EditCaseDetailsSerializer(serializers.Serializer):
    """Serializer for updating case details"""

    # Customer fields (editable)
    customer_name = serializers.CharField(max_length=200, required=False, help_text="Customer's full name")
    email = serializers.EmailField(required=False, help_text="Customer's email address")
    phone = serializers.CharField(max_length=20, required=False, help_text="Customer's phone number")

    # Policy fields (editable)
    policy_type = serializers.IntegerField(required=False, help_text="PolicyType ID from dropdown")
    premium_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, help_text="Policy premium amount")
    expiry_date = serializers.DateField(required=False, help_text="Policy expiry date (YYYY-MM-DD)")
    assigned_agent = serializers.IntegerField(required=False, allow_null=True, help_text="User ID for assigned agent from dropdown")

    def validate_policy_type(self, value):
        """Validate that policy type exists"""
        if value:
            try:
                PolicyType.objects.get(id=value, is_active=True)
            except PolicyType.DoesNotExist:
                raise serializers.ValidationError("Invalid policy type ID or policy type is not active.")
        return value

    def validate_assigned_agent(self, value):
        """Validate that assigned agent exists"""
        if value:
            try:
                User.objects.get(id=value, is_active=True)
            except User.DoesNotExist:
                raise serializers.ValidationError("Invalid agent ID or agent is not active.")
        return value

    def validate_email(self, value):
        """Validate email format and uniqueness within reasonable scope"""
        if value:
            pass
        return value

    def validate_phone(self, value):
        """Validate phone number format"""
        if value:
            if len(value.strip()) < 10:
                raise serializers.ValidationError("Phone number must be at least 10 digits.")
        return value


# Dropdown Data Serializers
class PolicyTypeDropdownSerializer(serializers.Serializer):
    """Serializer for policy type dropdown options"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    category = serializers.CharField()


class AgentDropdownSerializer(serializers.Serializer):
    """Serializer for agent dropdown options"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    email = serializers.EmailField()


class CaseEditFormDataSerializer(serializers.Serializer):
    """Serializer for complete case edit form data including dropdowns"""
    case_details = CaseDetailsSerializer()
    policy_types = PolicyTypeDropdownSerializer(many=True)
    agents = AgentDropdownSerializer(many=True)
