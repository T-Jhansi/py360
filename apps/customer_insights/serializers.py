"""
Serializers for Customer Insights API endpoints.
"""

from rest_framework import serializers
from django.utils import timezone
from .models import (
    CustomerInsight, PaymentInsight, CommunicationInsight, 
    ClaimsInsight, CustomerProfileInsight
)
from apps.customers.models import Customer


class CustomerBasicInfoSerializer(serializers.ModelSerializer):
    """Serializer for basic customer information"""
    
    full_name = serializers.CharField(read_only=True)
    customer_since = serializers.SerializerMethodField()
    
    class Meta:
        model = Customer
        fields = [
            'id', 'customer_code', 'full_name', 'email', 'phone',
            'status', 'priority', 'profile', 'customer_since',
            'total_policies', 'total_premium'
        ]
    
    def get_customer_since(self, obj):
        """Get customer since date"""
        return obj.first_policy_date


class PaymentInsightSerializer(serializers.ModelSerializer):
    """Serializer for payment insights"""
    
    total_premiums_paid = serializers.DecimalField(max_digits=15, decimal_places=2)
    average_payment_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    class Meta:
        model = PaymentInsight
        fields = [
            'total_premiums_paid', 'on_time_payment_rate', 'total_payments_made',
            'most_used_mode', 'average_payment_timing', 'payment_reliability',
            'preferred_payment_method', 'average_payment_amount', 'customer_since_years',
            'last_payment_date', 'payment_frequency'
        ]


class CommunicationInsightSerializer(serializers.ModelSerializer):
    """Serializer for communication insights"""
    
    channel_breakdown = serializers.JSONField()
    
    class Meta:
        model = CommunicationInsight
        fields = [
            'total_communications', 'avg_response_time', 'satisfaction_rating',
            'last_contact_date', 'channel_breakdown', 'preferred_channel',
            'communication_frequency', 'response_rate', 'escalation_count'
        ]


class ClaimsInsightSerializer(serializers.ModelSerializer):
    """Serializer for claims insights"""
    
    approved_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_claimed_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    claims_by_type = serializers.JSONField()
    claims_by_status = serializers.JSONField()
    
    class Meta:
        model = ClaimsInsight
        fields = [
            'total_claims', 'approved_amount', 'avg_processing_time', 'approval_rate',
            'claims_by_type', 'claims_by_status', 'risk_level', 'last_claim_date',
            'claim_frequency', 'total_claimed_amount'
        ]


class CustomerProfileInsightSerializer(serializers.ModelSerializer):
    """Serializer for customer profile insights"""
    
    customer_lifetime_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_paid_ytd = serializers.DecimalField(max_digits=15, decimal_places=2)
    policy_portfolio = serializers.JSONField()
    
    class Meta:
        model = CustomerProfileInsight
        fields = [
            'active_policies', 'family_policies', 'expired_lapsed_policies',
            'customer_lifetime_value', 'total_paid_ytd', 'customer_segment',
            'engagement_level', 'policy_portfolio', 'overall_risk_score'
        ]


class PaymentScheduleSerializer(serializers.Serializer):
    """Serializer for payment schedule data"""
    
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    due_date = serializers.DateField()
    policy = serializers.CharField()
    days_until_due = serializers.IntegerField()
    status = serializers.CharField()


class PaymentHistorySerializer(serializers.Serializer):
    """Serializer for payment history data"""
    
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    date = serializers.DateTimeField()
    status = serializers.CharField()
    mode = serializers.CharField()
    policy = serializers.CharField()


class YearlyPaymentSummarySerializer(serializers.Serializer):
    """Serializer for yearly payment summary"""
    
    year = serializers.IntegerField()
    total = serializers.DecimalField(max_digits=15, decimal_places=2)
    payments_count = serializers.IntegerField()
    payments = PaymentHistorySerializer(many=True)


class PaymentHistoryResponseSerializer(serializers.Serializer):
    """Serializer for payment history response"""
    
    yearly_breakdown = YearlyPaymentSummarySerializer(many=True)
    summary = serializers.DictField()


class CommunicationHistorySerializer(serializers.Serializer):
    """Serializer for communication history"""
    
    id = serializers.IntegerField()
    date = serializers.DateTimeField()
    channel = serializers.CharField()
    outcome = serializers.CharField()
    message_content = serializers.CharField()
    response_received = serializers.CharField(required=False)


class CommunicationHistoryResponseSerializer(serializers.Serializer):
    """Serializer for communication history response"""
    
    total_communications = serializers.IntegerField()
    by_channel = serializers.DictField()
    recent_communications = CommunicationHistorySerializer(many=True)


class ClaimHistorySerializer(serializers.Serializer):
    """Serializer for claim history"""
    
    id = serializers.IntegerField()
    title = serializers.CharField()
    type = serializers.CharField()
    status = serializers.CharField()
    claim_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    approved_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    incident_date = serializers.DateField()
    claim_number = serializers.CharField()
    adjuster = serializers.CharField()
    rejection_reason = serializers.CharField(required=False)


class ClaimsHistoryResponseSerializer(serializers.Serializer):
    """Serializer for claims history response"""
    
    claims = ClaimHistorySerializer(many=True)
    summary = serializers.DictField()


class CustomerInsightsResponseSerializer(serializers.Serializer):
    """Main serializer for customer insights response"""
    
    customer_info = CustomerBasicInfoSerializer()
    payment_insights = PaymentInsightSerializer()
    communication_insights = CommunicationInsightSerializer()
    claims_insights = ClaimsInsightSerializer()
    profile_insights = CustomerProfileInsightSerializer()
    payment_schedule = serializers.DictField()
    payment_history = PaymentHistoryResponseSerializer()


class PaymentScheduleResponseSerializer(serializers.Serializer):
    """Serializer for payment schedule response"""
    
    upcoming_payments = PaymentScheduleSerializer(many=True)
    next_payment = PaymentScheduleSerializer(required=False)


class CustomerInsightSerializer(serializers.ModelSerializer):
    """Serializer for CustomerInsight model"""
    
    customer = CustomerBasicInfoSerializer(read_only=True)
    insight_type_display = serializers.CharField(source='get_insight_type_display', read_only=True)
    
    class Meta:
        model = CustomerInsight
        fields = [
            'id', 'customer', 'insight_type', 'insight_type_display',
            'calculated_at', 'data', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'calculated_at']


class CustomerInsightsSummarySerializer(serializers.Serializer):
    """Serializer for customer insights summary"""
    
    customer_id = serializers.IntegerField()
    customer_name = serializers.CharField()
    customer_code = serializers.CharField()
    total_premiums_paid = serializers.DecimalField(max_digits=15, decimal_places=2)
    on_time_payment_rate = serializers.FloatField()
    total_communications = serializers.IntegerField()
    satisfaction_rating = serializers.FloatField()
    total_claims = serializers.IntegerField()
    approval_rate = serializers.FloatField()
    risk_level = serializers.CharField()
    customer_segment = serializers.CharField()
    last_updated = serializers.DateTimeField()


class InsightsDashboardSerializer(serializers.Serializer):
    """Serializer for insights dashboard data"""
    
    total_customers = serializers.IntegerField()
    high_value_customers = serializers.IntegerField()
    customers_with_claims = serializers.IntegerField()
    avg_satisfaction_rating = serializers.FloatField()
    total_premiums_collected = serializers.DecimalField(max_digits=15, decimal_places=2)
    payment_reliability_avg = serializers.FloatField()
    recent_insights = CustomerInsightsSummarySerializer(many=True)


class CustomerInsightsFilterSerializer(serializers.Serializer):
    """Serializer for filtering customer insights"""
    
    customer_segment = serializers.CharField(required=False)
    risk_level = serializers.CharField(required=False)
    payment_reliability = serializers.CharField(required=False)
    engagement_level = serializers.CharField(required=False)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    limit = serializers.IntegerField(default=50, max_value=100)
    offset = serializers.IntegerField(default=0, min_value=0)


class CustomerInsightsBulkUpdateSerializer(serializers.Serializer):
    """Serializer for bulk updating customer insights"""
    
    customer_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=100
    )
    force_recalculate = serializers.BooleanField(default=False)
