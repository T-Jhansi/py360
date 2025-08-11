from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import BaseModel
from apps.policies.models import Policy

User = get_user_model()


class PolicyAdditionalBenefit(BaseModel):
    """Model to store additional benefits for different policies"""
    
    BENEFIT_TYPE_CHOICES = [
        ('key_replacement', 'Key Replacement'),
        ('return_to_invoice', 'Return to Invoice'),
        ('personal_accident', 'Personal Accident'),
        ('passenger_cover', 'Passenger Cover'),
        ('consumables_cover', 'Consumables Cover'),
        ('roadside_assistance', 'Roadside Assistance'),
        ('zero_depreciation', 'Zero Depreciation'),
        ('engine_protection', 'Engine Protection'),
        ('ncb_protection', 'NCB Protection'),
        ('emergency_support', 'Emergency Support'),
        ('medical_expenses', 'Medical Expenses'),
        ('legal_liability', 'Legal Liability'),
        ('towing_charges', 'Towing Charges'),
        ('daily_allowance', 'Daily Allowance'),
        ('general', 'General'),
    ]
    
    policy = models.ForeignKey(
        Policy, 
        on_delete=models.CASCADE, 
        related_name='policy_additional_benefits',
        help_text="Policy this benefit belongs to"
    )
    
    benefit_type = models.CharField(
        max_length=50, 
        choices=BENEFIT_TYPE_CHOICES,
        default='general',
        db_index=True,
        help_text="Type of additional benefit"
    )
    
    benefit_name = models.CharField(
        max_length=200,
        help_text="Name of the additional benefit"
    )
    
    benefit_description = models.TextField(
        help_text="Detailed description of the benefit"
    )
    
    benefit_value = models.CharField(
        max_length=500,
        blank=True,
        help_text="Value or amount associated with the benefit (if applicable)"
    )
    
    coverage_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Coverage amount for this benefit"
    )
    
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this benefit is currently active"
    )
    
    is_optional = models.BooleanField(
        default=True,
        help_text="Whether this benefit is optional or mandatory"
    )
    
    premium_impact = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Additional premium for this benefit"
    )
    
    display_order = models.PositiveIntegerField(
        default=0,
        help_text="Order in which to display this benefit"
    )
    
    terms_conditions = models.TextField(
        blank=True,
        help_text="Specific terms and conditions for this benefit"
    )
    
    additional_info = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional information about the benefit"
    )
    
    class Meta:
        db_table = 'policy_additional_benefits'
        ordering = ['display_order', 'benefit_name']
        indexes = [
            models.Index(fields=['policy', 'is_active']),
            models.Index(fields=['benefit_type', 'is_active']),
            models.Index(fields=['policy', 'benefit_type']),
            models.Index(fields=['display_order']),
        ]
        unique_together = ['policy', 'benefit_name']
    
    def __str__(self):
        return f"{self.policy.policy_number} - {self.benefit_name}"
    
    @property
    def policy_number(self):
        """Return the policy number for easy access"""
        return self.policy.policy_number if self.policy else None
    
    @property
    def customer_name(self):
        """Return the customer name for easy access"""
        return self.policy.customer.name if self.policy and self.policy.customer else None
