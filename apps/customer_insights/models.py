"""
Customer Insights models for the Intelipro Insurance Policy Renewal System.
"""

from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import BaseModel
from apps.customers.models import Customer

User = get_user_model()


class CustomerInsight(BaseModel):
    """Main customer insights aggregation"""
    
    INSIGHT_TYPE_CHOICES = [
        ('payment', 'Payment Insights'),
        ('communication', 'Communication Insights'),
        ('claims', 'Claims Insights'),
        ('profile', 'Customer Profile'),
        ('behavior', 'Behavior Analysis'),
    ]
    
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='customer_insights',
        help_text="Customer these insights belong to"
    )
    
    insight_type = models.CharField(
        max_length=50,
        choices=INSIGHT_TYPE_CHOICES,
        db_index=True,
        help_text="Type of insight"
    )
    
    calculated_at = models.DateTimeField(
        auto_now=True,
        help_text="When these insights were last calculated"
    )
    
    data = models.JSONField(
        default=dict,
        help_text="Structured insight data"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this insight is currently active"
    )
    
    class Meta:
        db_table = 'customer_insights'
        ordering = ['-calculated_at']
        indexes = [
            models.Index(fields=['customer', 'insight_type']),
            models.Index(fields=['calculated_at']),
            models.Index(fields=['is_active']),
        ]
        unique_together = ['customer', 'insight_type']
    
    def __str__(self):
        return f"{self.customer} - {self.get_insight_type_display()}"


class PaymentInsight(BaseModel):
    """Payment-specific insights for customers"""
    
    PAYMENT_RELIABILITY_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('average', 'Average'),
        ('poor', 'Poor'),
    ]
    
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='payment_insights',
        help_text="Customer these payment insights belong to"
    )
    
    # Payment Statistics
    total_premiums_paid = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Total premiums paid by customer"
    )
    
    on_time_payment_rate = models.FloatField(
        default=0.0,
        help_text="Percentage of on-time payments"
    )
    
    total_payments_made = models.PositiveIntegerField(
        default=0,
        help_text="Total number of payments made"
    )
    
    most_used_mode = models.CharField(
        max_length=50,
        blank=True,
        help_text="Most frequently used payment method"
    )
    
    average_payment_timing = models.CharField(
        max_length=100,
        blank=True,
        help_text="Average payment timing (e.g., '5 days early')"
    )
    
    payment_reliability = models.CharField(
        max_length=20,
        choices=PAYMENT_RELIABILITY_CHOICES,
        default='average',
        help_text="Overall payment reliability rating"
    )
    
    # Payment Patterns
    preferred_payment_method = models.CharField(
        max_length=50,
        blank=True,
        help_text="Customer's preferred payment method"
    )
    
    average_payment_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Average payment amount"
    )
    
    # Time-based metrics
    customer_since_years = models.PositiveIntegerField(
        default=0,
        help_text="Number of years as customer"
    )
    
    last_payment_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date of last payment"
    )
    
    # Calculated fields
    payment_frequency = models.CharField(
        max_length=50,
        blank=True,
        help_text="Payment frequency pattern"
    )
    
    class Meta:
        db_table = 'payment_insights'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer']),
            models.Index(fields=['payment_reliability']),
            models.Index(fields=['on_time_payment_rate']),
        ]
    
    def __str__(self):
        return f"Payment Insights - {self.customer}"


class CommunicationInsight(BaseModel):
    """Communication-specific insights for customers"""
    
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='communication_insights',
        help_text="Customer these communication insights belong to"
    )
    
    # Communication Statistics
    total_communications = models.PositiveIntegerField(
        default=0,
        help_text="Total number of communications"
    )
    
    avg_response_time = models.FloatField(
        default=0.0,
        help_text="Average response time in hours"
    )
    
    satisfaction_rating = models.FloatField(
        default=0.0,
        help_text="Average satisfaction rating (1-5)"
    )
    
    last_contact_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date of last contact"
    )
    
    # Channel breakdown
    channel_breakdown = models.JSONField(
        default=dict,
        help_text="Communication breakdown by channel"
    )
    
    # Communication patterns
    preferred_channel = models.CharField(
        max_length=50,
        blank=True,
        help_text="Customer's preferred communication channel"
    )
    
    communication_frequency = models.CharField(
        max_length=50,
        blank=True,
        help_text="Communication frequency pattern"
    )
    
    # Response metrics
    response_rate = models.FloatField(
        default=0.0,
        help_text="Customer response rate percentage"
    )
    
    escalation_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of escalated communications"
    )
    
    class Meta:
        db_table = 'communication_insights'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer']),
            models.Index(fields=['satisfaction_rating']),
            models.Index(fields=['last_contact_date']),
        ]
    
    def __str__(self):
        return f"Communication Insights - {self.customer}"


class ClaimsInsight(BaseModel):
    """Claims-specific insights for customers"""
    
    RISK_LEVEL_CHOICES = [
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
    ]
    
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='claims_insights',
        help_text="Customer these claims insights belong to"
    )
    
    # Claims Statistics
    total_claims = models.PositiveIntegerField(
        default=0,
        help_text="Total number of claims"
    )
    
    approved_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Total approved claim amount"
    )
    
    avg_processing_time = models.PositiveIntegerField(
        default=0,
        help_text="Average processing time in days"
    )
    
    approval_rate = models.FloatField(
        default=0.0,
        help_text="Claim approval rate percentage"
    )
    
    # Claims breakdown
    claims_by_type = models.JSONField(
        default=dict,
        help_text="Claims breakdown by type"
    )
    
    claims_by_status = models.JSONField(
        default=dict,
        help_text="Claims breakdown by status"
    )
    
    # Risk assessment
    risk_level = models.CharField(
        max_length=20,
        choices=RISK_LEVEL_CHOICES,
        default='low',
        help_text="Overall claims risk level"
    )
    
    # Time-based metrics
    last_claim_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date of last claim"
    )
    
    claim_frequency = models.CharField(
        max_length=50,
        blank=True,
        help_text="Claim frequency pattern"
    )
    
    # Financial impact
    total_claimed_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Total amount claimed"
    )
    
    class Meta:
        db_table = 'claims_insights'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer']),
            models.Index(fields=['risk_level']),
            models.Index(fields=['approval_rate']),
        ]
    
    def __str__(self):
        return f"Claims Insights - {self.customer}"


class CustomerProfileInsight(BaseModel):
    """Comprehensive customer profile insights"""
    
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='profile_insights',
        help_text="Customer these profile insights belong to"
    )
    
    # Customer metrics
    active_policies = models.PositiveIntegerField(
        default=0,
        help_text="Number of active policies"
    )
    
    family_policies = models.PositiveIntegerField(
        default=0,
        help_text="Number of family policies"
    )
    
    expired_lapsed_policies = models.PositiveIntegerField(
        default=0,
        help_text="Number of expired/lapsed policies"
    )
    
    # Customer value
    customer_lifetime_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Customer lifetime value"
    )
    
    total_paid_ytd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Total paid year-to-date"
    )
    
    # Customer behavior
    customer_segment = models.CharField(
        max_length=50,
        blank=True,
        help_text="Customer segment classification"
    )
    
    engagement_level = models.CharField(
        max_length=50,
        blank=True,
        help_text="Customer engagement level"
    )
    
    # Portfolio analysis
    policy_portfolio = models.JSONField(
        default=dict,
        help_text="Customer's policy portfolio breakdown"
    )
    
    # Risk profile
    overall_risk_score = models.FloatField(
        default=0.0,
        help_text="Overall risk score (0-100)"
    )
    
    class Meta:
        db_table = 'customer_profile_insights'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer']),
            models.Index(fields=['customer_segment']),
            models.Index(fields=['engagement_level']),
        ]
    
    def __str__(self):
        return f"Profile Insights - {self.customer}"
