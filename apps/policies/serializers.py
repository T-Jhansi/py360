from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    PolicyType, Policy, PolicyRenewal, PolicyClaim, 
    PolicyDocument, PolicyBeneficiary, PolicyPayment, PolicyNote
)
from apps.customers.models import Customer

User = get_user_model()

class PolicyTypeSerializer(serializers.ModelSerializer):
    """Serializer for PolicyType model"""
    
    class Meta:
        model = PolicyType
        fields = [
            'id', 'name', 'code', 'description', 'is_active',
            'base_premium_rate', 'coverage_details', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class PolicyBeneficiarySerializer(serializers.ModelSerializer):
    """Serializer for PolicyBeneficiary model"""
    
    class Meta:
        model = PolicyBeneficiary
        fields = [
            'id', 'name', 'relationship', 'contact_number', 'email', 'address',
            'date_of_birth', 'id_type', 'id_number', 'percentage_share',
            'is_primary', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class PolicyDocumentSerializer(serializers.ModelSerializer):
    """Serializer for PolicyDocument model"""
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.get_full_name', read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = PolicyDocument
        fields = [
            'id', 'document_type', 'document_name', 'file', 'file_url', 'file_size', 
            'mime_type', 'description', 'is_verified', 'verified_by', 'verified_by_name',
            'verified_at', 'uploaded_by', 'uploaded_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'file_size', 'mime_type', 'created_at', 'updated_at']
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
        return None

class PolicyPaymentSerializer(serializers.ModelSerializer):
    """Serializer for PolicyPayment model"""
    processed_by_name = serializers.CharField(source='processed_by.get_full_name', read_only=True)
    
    class Meta:
        model = PolicyPayment
        fields = [
            'id', 'payment_date', 'amount', 'payment_method', 'status',
            'transaction_id', 'payment_reference', 'gateway_response',
            'payment_for_period_start', 'payment_for_period_end', 'notes',
            'processed_by', 'processed_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class PolicyNoteSerializer(serializers.ModelSerializer):
    """Serializer for PolicyNote model"""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = PolicyNote
        fields = [
            'id', 'note', 'is_customer_visible', 'note_type',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

class PolicySerializer(serializers.ModelSerializer):
    """Main Policy serializer"""
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    customer_email = serializers.CharField(source='customer.email', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone_number', read_only=True)
    policy_type_name = serializers.CharField(source='policy_type.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    last_modified_by_name = serializers.CharField(source='last_modified_by.get_full_name', read_only=True)
    
    # Nested relationships
    beneficiaries = PolicyBeneficiarySerializer(many=True, read_only=True)
    documents = PolicyDocumentSerializer(many=True, read_only=True, context={'request': None})
    payments = PolicyPaymentSerializer(many=True, read_only=True)
    notes = PolicyNoteSerializer(many=True, read_only=True)
    
    # Computed fields
    is_due_for_renewal = serializers.ReadOnlyField()
    days_to_expiry = serializers.ReadOnlyField()
    
    class Meta:
        model = Policy
        fields = [
            'id', 'policy_number', 'customer', 'customer_name', 'customer_email', 'customer_phone',
            'policy_type', 'policy_type_name', 'start_date', 'end_date', 'premium_amount',
            'sum_assured', 'status', 'payment_frequency', 'nominee_name', 'nominee_relationship',
            'nominee_contact', 'policy_document', 'terms_conditions', 'special_conditions',
            'agent_name', 'agent_code', 'created_by', 'created_by_name', 'last_modified_by',
            'last_modified_by_name', 'is_due_for_renewal', 'days_to_expiry',
            'beneficiaries', 'documents', 'payments', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_due_for_renewal', 'days_to_expiry']

class PolicyListSerializer(serializers.ModelSerializer):
    """Simplified serializer for policy lists"""
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    policy_type_name = serializers.CharField(source='policy_type.name', read_only=True)
    is_due_for_renewal = serializers.ReadOnlyField()
    days_to_expiry = serializers.ReadOnlyField()
    
    class Meta:
        model = Policy
        fields = [
            'id', 'policy_number', 'customer_name', 'policy_type_name',
            'start_date', 'end_date', 'premium_amount', 'status',
            'is_due_for_renewal', 'days_to_expiry', 'created_at'
        ]

class PolicyRenewalSerializer(serializers.ModelSerializer):
    """Serializer for PolicyRenewal model"""
    policy_number = serializers.CharField(source='policy.policy_number', read_only=True)
    customer_name = serializers.CharField(source='policy.customer.full_name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    
    class Meta:
        model = PolicyRenewal
        fields = [
            'id', 'policy', 'policy_number', 'customer_name', 'renewal_date',
            'new_premium_amount', 'new_sum_assured', 'status', 'renewal_notice_sent',
            'renewal_notice_date', 'customer_response', 'contact_attempts',
            'last_contact_date', 'contact_method', 'notes', 'assigned_to',
            'assigned_to_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class PolicyClaimSerializer(serializers.ModelSerializer):
    """Serializer for PolicyClaim model"""
    policy_number = serializers.CharField(source='policy.policy_number', read_only=True)
    customer_name = serializers.CharField(source='policy.customer.full_name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    
    class Meta:
        model = PolicyClaim
        fields = [
            'id', 'claim_number', 'policy', 'policy_number', 'customer_name',
            'claim_type', 'claim_amount', 'approved_amount', 'incident_date',
            'claim_date', 'status', 'description', 'assigned_to', 'assigned_to_name',
            'review_notes', 'rejection_reason', 'payment_date', 'payment_reference',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

# Create/Update serializers with validation
class PolicyCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new policies"""
    
    class Meta:
        model = Policy
        fields = [
            'policy_number', 'customer', 'policy_type', 'start_date', 'end_date',
            'premium_amount', 'sum_assured', 'payment_frequency', 'nominee_name',
            'nominee_relationship', 'nominee_contact', 'terms_conditions',
            'special_conditions', 'agent_name', 'agent_code'
        ]
    
    def validate_policy_number(self, value):
        """Ensure policy number is unique"""
        if Policy.objects.filter(policy_number=value).exists():
            raise serializers.ValidationError("Policy number already exists.")
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        if data['end_date'] <= data['start_date']:
            raise serializers.ValidationError("End date must be after start date.")
        
        if data['premium_amount'] <= 0:
            raise serializers.ValidationError("Premium amount must be greater than 0.")
        
        if data['sum_assured'] <= 0:
            raise serializers.ValidationError("Sum assured must be greater than 0.")
        
        return data

class PolicyRenewalCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating policy renewals"""
    
    class Meta:
        model = PolicyRenewal
        fields = [
            'policy', 'renewal_date', 'new_premium_amount', 'new_sum_assured',
            'notes', 'assigned_to'
        ]
    
    def validate(self, data):
        """Validate renewal data"""
        if data['new_premium_amount'] <= 0:
            raise serializers.ValidationError("New premium amount must be greater than 0.")
        
        if data['new_sum_assured'] <= 0:
            raise serializers.ValidationError("New sum assured must be greater than 0.")
        
        return data

class PolicyClaimCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating policy claims"""
    
    class Meta:
        model = PolicyClaim
        fields = [
            'claim_number', 'policy', 'claim_type', 'claim_amount',
            'incident_date', 'claim_date', 'description'
        ]
    
    def validate_claim_number(self, value):
        """Ensure claim number is unique"""
        if PolicyClaim.objects.filter(claim_number=value).exists():
            raise serializers.ValidationError("Claim number already exists.")
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        if data['claim_amount'] <= 0:
            raise serializers.ValidationError("Claim amount must be greater than 0.")
        
        if data['claim_date'] < data['incident_date']:
            raise serializers.ValidationError("Claim date cannot be before incident date.")
        
        return data

# Dashboard serializers
class PolicyDashboardSerializer(serializers.Serializer):
    """Serializer for policy dashboard statistics"""
    total_policies = serializers.IntegerField()
    active_policies = serializers.IntegerField()
    expired_policies = serializers.IntegerField()
    pending_renewals = serializers.IntegerField()
    total_premium_collected = serializers.DecimalField(max_digits=15, decimal_places=2)
    policies_due_for_renewal = serializers.IntegerField()
    recent_claims = serializers.IntegerField()

class RenewalDashboardSerializer(serializers.Serializer):
    """Serializer for renewal dashboard statistics"""
    pending_renewals = serializers.IntegerField()
    in_progress_renewals = serializers.IntegerField()
    completed_renewals = serializers.IntegerField()
    overdue_renewals = serializers.IntegerField()
    renewal_rate = serializers.DecimalField(max_digits=5, decimal_places=2) 