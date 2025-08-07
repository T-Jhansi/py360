from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import BaseModel
from apps.customers.models import Customer
from apps.policies.models import Policy

User = get_user_model()


class AIInsight(BaseModel):
    
    INSIGHT_TYPE_CHOICES = [
        ('claim_likelihood', 'Claim Likelihood'),
        ('customer_profile', 'Customer Profile'),
        ('renewal_prediction', 'Renewal Prediction'),
        ('risk_assessment', 'Risk Assessment'),
        ('behavior_analysis', 'Behavior Analysis'),
        ('payment_pattern', 'Payment Pattern'),
    ]
    
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='ai_insights',
        help_text="Customer this insight is about"
    )
    policy = models.ForeignKey(
        Policy,
        on_delete=models.CASCADE,
        related_name='ai_insights',
        null=True,
        blank=True,
        help_text="Policy this insight is about (optional for customer-level insights)"
    )
    insight_type = models.CharField(
        max_length=50,
        choices=INSIGHT_TYPE_CHOICES,
        db_index=True,
        help_text="Type of AI insight"
    )
    insight_title = models.CharField(
        max_length=200,
        help_text="Title of the insight (e.g., 'Claim Likelihood', 'Customer Profile')"
    )
    insight_value = models.CharField(
        max_length=100,
        help_text="Value or result of the insight (e.g., 'Moderate', 'Good', 'High Risk')"
    )
    insight_description = models.TextField(
        help_text="Detailed explanation of the insight"
    )
    confidence_score = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="AI confidence level (0.0000 to 1.0000)"
    )
    key_observations = models.JSONField(
        default=dict,
        help_text="Structured data for key observations and metrics"
    )
    generated_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this insight was generated"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this insight should be displayed"
    )
    
    class Meta:
        db_table = 'ai_insights'
        ordering = ['-generated_at', 'insight_type']
        indexes = [
            models.Index(fields=['customer', 'insight_type']),
            models.Index(fields=['policy', 'insight_type']),
            models.Index(fields=['generated_at']),
        ]
    
    def __str__(self):
        policy_info = f" - {self.policy.policy_number}" if self.policy else ""
        return f"{self.insight_title} for {self.customer.name}{policy_info}"


class AIInsightHistory(BaseModel):
    
    insight = models.ForeignKey(
        AIInsight,
        on_delete=models.CASCADE,
        related_name='history',
        help_text="The insight this history entry belongs to"
    )
    previous_value = models.CharField(
        max_length=100,
        help_text="Previous insight value"
    )
    new_value = models.CharField(
        max_length=100,
        help_text="New insight value"
    )
    previous_confidence = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Previous confidence score"
    )
    new_confidence = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="New confidence score"
    )
    change_reason = models.TextField(
        blank=True,
        help_text="Reason for the change in insight"
    )
    changed_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this change occurred"
    )
    
    class Meta:
        db_table = 'ai_insights_history'
        ordering = ['-changed_at']
    
    def __str__(self):
        return f"History for {self.insight.insight_title} - {self.changed_at}"
