"""
Serializers for Other Insurance Policies app.
"""

from rest_framework import serializers
from .models import OtherInsurancePolicy
from apps.customers.models import Customer
from apps.policies.models import PolicyType


class OtherInsurancePolicySerializer(serializers.ModelSerializer):
    """Serializer for OtherInsurancePolicy model"""
    
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    customer_code = serializers.CharField(source='customer.customer_code', read_only=True)
    customer_email = serializers.CharField(source='customer.email', read_only=True)
    policy_type_name = serializers.CharField(source='policy_type.name', read_only=True)
    policy_type_category = serializers.CharField(source='policy_type.category', read_only=True)
    policy_summary = serializers.CharField(read_only=True)
    annual_premium = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    is_expiring_soon = serializers.BooleanField(read_only=True)
    days_to_expiry = serializers.IntegerField(read_only=True)
    policy_age_years = serializers.FloatField(read_only=True)
    competitive_analysis_score = serializers.IntegerField(read_only=True)
    risk_indicators = serializers.ListField(read_only=True)
    
    class Meta:
        model = OtherInsurancePolicy
        fields = [
            'id',
            'customer',
            'customer_name',
            'customer_code',
            'customer_email',
            'policy_type',
            'policy_type_name',
            'policy_type_category',
            'policy_number',
            'insurance_company',
            'policy_status',
            'start_date',
            'end_date',
            'next_renewal_date',
            'premium_amount',
            'sum_assured',
            'payment_mode',
            'nominee_name',
            'nominee_relationship',
            'agent_name',
            'agent_contact',
            'channel',
            'policy_features',
            'riders',
            'exclusions',
            'special_conditions',
            'satisfaction_rating',
            'claim_experience',
            'is_renewal_interested',
            'renewal_concerns',
            'competitor_advantages',
            'switching_potential',
            'notes',
            'last_updated_by_customer',
            'verification_status',
            'policy_summary',
            'annual_premium',
            'is_expiring_soon',
            'days_to_expiry',
            'policy_age_years',
            'competitive_analysis_score',
            'risk_indicators',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class OtherInsurancePolicyCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating OtherInsurancePolicy"""
    
    class Meta:
        model = OtherInsurancePolicy
        fields = [
            'customer',
            'policy_type',
            'policy_number',
            'insurance_company',
            'policy_status',
            'start_date',
            'end_date',
            'next_renewal_date',
            'premium_amount',
            'sum_assured',
            'payment_mode',
            'nominee_name',
            'nominee_relationship',
            'agent_name',
            'agent_contact',
            'channel',
            'policy_features',
            'riders',
            'exclusions',
            'special_conditions',
            'satisfaction_rating',
            'claim_experience',
            'is_renewal_interested',
            'renewal_concerns',
            'competitor_advantages',
            'switching_potential',
            'notes',
            'last_updated_by_customer',
            'verification_status',
        ]
    
    def validate(self, data):
        """Validate the policy data"""
        # Validate dates
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and start_date >= end_date:
            raise serializers.ValidationError(
                "End date must be after start date."
            )
        
        # Validate premium amount
        premium_amount = data.get('premium_amount')
        if premium_amount and premium_amount <= 0:
            raise serializers.ValidationError(
                "Premium amount must be greater than zero."
            )
        
        # Validate sum assured
        sum_assured = data.get('sum_assured')
        if sum_assured and sum_assured <= 0:
            raise serializers.ValidationError(
                "Sum assured must be greater than zero."
            )
        
        # Validate satisfaction rating
        satisfaction_rating = data.get('satisfaction_rating')
        if satisfaction_rating and (satisfaction_rating < 1 or satisfaction_rating > 5):
            raise serializers.ValidationError(
                "Satisfaction rating must be between 1 and 5."
            )
        
        # Check for duplicate policy
        customer = data.get('customer')
        policy_number = data.get('policy_number')
        insurance_company = data.get('insurance_company')
        
        if customer and policy_number and insurance_company:
            existing = OtherInsurancePolicy.objects.filter(
                customer=customer,
                policy_number=policy_number,
                insurance_company=insurance_company,
                is_deleted=False
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if existing.exists():
                raise serializers.ValidationError(
                    "A policy with this number already exists for this customer with the same insurance company."
                )
        
        return data


class OtherInsurancePolicyUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating OtherInsurancePolicy"""
    
    class Meta:
        model = OtherInsurancePolicy
        fields = [
            'policy_status',
            'end_date',
            'next_renewal_date',
            'premium_amount',
            'sum_assured',
            'payment_mode',
            'nominee_name',
            'nominee_relationship',
            'agent_name',
            'agent_contact',
            'channel',
            'policy_features',
            'riders',
            'exclusions',
            'special_conditions',
            'satisfaction_rating',
            'claim_experience',
            'is_renewal_interested',
            'renewal_concerns',
            'competitor_advantages',
            'switching_potential',
            'notes',
            'last_updated_by_customer',
            'verification_status',
        ]
    
    def validate(self, data):
        """Validate the policy data"""
        # Validate dates
        end_date = data.get('end_date', self.instance.end_date if self.instance else None)
        start_date = self.instance.start_date if self.instance else None
        
        if start_date and end_date and start_date >= end_date:
            raise serializers.ValidationError(
                "End date must be after start date."
            )
        
        # Validate premium amount
        premium_amount = data.get('premium_amount', self.instance.premium_amount if self.instance else None)
        if premium_amount and premium_amount <= 0:
            raise serializers.ValidationError(
                "Premium amount must be greater than zero."
            )
        
        # Validate sum assured
        sum_assured = data.get('sum_assured', self.instance.sum_assured if self.instance else None)
        if sum_assured and sum_assured <= 0:
            raise serializers.ValidationError(
                "Sum assured must be greater than zero."
            )
        
        # Validate satisfaction rating
        satisfaction_rating = data.get('satisfaction_rating', self.instance.satisfaction_rating if self.instance else None)
        if satisfaction_rating and (satisfaction_rating < 1 or satisfaction_rating > 5):
            raise serializers.ValidationError(
                "Satisfaction rating must be between 1 and 5."
            )
        
        return data


class OtherInsurancePolicyListSerializer(serializers.ModelSerializer):
    """Serializer for listing OtherInsurancePolicy with minimal data"""
    
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    customer_code = serializers.CharField(source='customer.customer_code', read_only=True)
    policy_type_name = serializers.CharField(source='policy_type.name', read_only=True)
    policy_type_category = serializers.CharField(source='policy_type.category', read_only=True)
    policy_summary = serializers.CharField(read_only=True)
    annual_premium = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    is_expiring_soon = serializers.BooleanField(read_only=True)
    days_to_expiry = serializers.IntegerField(read_only=True)
    competitive_analysis_score = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = OtherInsurancePolicy
        fields = [
            'id',
            'customer',
            'customer_name',
            'customer_code',
            'policy_type',
            'policy_type_name',
            'policy_type_category',
            'policy_number',
            'insurance_company',
            'policy_status',
            'start_date',
            'end_date',
            'premium_amount',
            'sum_assured',
            'payment_mode',
            'satisfaction_rating',
            'switching_potential',
            'verification_status',
            'policy_summary',
            'annual_premium',
            'is_expiring_soon',
            'days_to_expiry',
            'competitive_analysis_score',
            'created_at',
        ]


class OtherInsurancePolicyCompetitiveAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for competitive analysis of other insurance policies"""
    
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    customer_code = serializers.CharField(source='customer.customer_code', read_only=True)
    policy_type_name = serializers.CharField(source='policy_type.name', read_only=True)
    policy_type_category = serializers.CharField(source='policy_type.category', read_only=True)
    policy_summary = serializers.CharField(read_only=True)
    annual_premium = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    competitive_analysis_score = serializers.IntegerField(read_only=True)
    risk_indicators = serializers.ListField(read_only=True)
    
    class Meta:
        model = OtherInsurancePolicy
        fields = [
            'id',
            'customer_name',
            'customer_code',
            'policy_type_name',
            'policy_type_category',
            'insurance_company',
            'policy_status',
            'sum_assured',
            'annual_premium',
            'satisfaction_rating',
            'claim_experience',
            'switching_potential',
            'is_renewal_interested',
            'competitor_advantages',
            'renewal_concerns',
            'policy_summary',
            'competitive_analysis_score',
            'risk_indicators',
            'verification_status',
            'created_at',
        ]


class OtherInsurancePolicySummarySerializer(serializers.ModelSerializer):
    """Serializer for policy summary and analytics"""
    
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    customer_code = serializers.CharField(source='customer.customer_code', read_only=True)
    policy_type_name = serializers.CharField(source='policy_type.name', read_only=True)
    policy_type_category = serializers.CharField(source='policy_type.category', read_only=True)
    policy_summary = serializers.CharField(read_only=True)
    annual_premium = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    is_expiring_soon = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = OtherInsurancePolicy
        fields = [
            'id',
            'customer_name',
            'customer_code',
            'policy_type_name',
            'policy_type_category',
            'insurance_company',
            'policy_status',
            'sum_assured',
            'annual_premium',
            'satisfaction_rating',
            'switching_potential',
            'policy_summary',
            'is_expiring_soon',
            'verification_status',
            'created_at',
        ]
