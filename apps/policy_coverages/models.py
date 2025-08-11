from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import BaseModel
from apps.policies.models import Policy

User = get_user_model()


class PolicyCoverage(BaseModel):
    """Model to store comprehensive policy coverage details"""
    
    COVERAGE_TYPE_CHOICES = [
        ('primary', 'Primary Coverage'),
        ('vehicle_protection', 'Vehicle Protection'),
        ('liability', 'Liability Coverage'),
        ('additional_benefit', 'Additional Benefit'),
        ('exclusion', 'Exclusion'),
        ('condition', 'Condition'),
    ]
    
    COVERAGE_CATEGORY_CHOICES = [
        ('comprehensive', 'Comprehensive Coverage'),
        ('own_damage', 'Own Damage'),
        ('engine_protection', 'Engine Protection'),
        ('zero_depreciation', 'Zero Depreciation'),
        ('third_party_liability', 'Third Party Liability'),
        ('personal_accident', 'Personal Accident'),
        ('passenger_coverage', 'Passenger Coverage'),
        ('legal_liability', 'Legal Liability'),
        ('enhanced_protection', 'Enhanced Protection'),
        ('addon_covers', 'Add-on Covers'),
        ('financial_benefits', 'Financial Benefits'),
        ('not_covered', 'Not Covered'),
        ('conditions_apply', 'Conditions Apply'),
    ]
    
    policy = models.ForeignKey(
        Policy, 
        on_delete=models.CASCADE, 
        related_name='policy_coverages',
        help_text="Policy this coverage belongs to"
    )
    
    coverage_type = models.CharField(
        max_length=50, 
        choices=COVERAGE_TYPE_CHOICES,
        default='primary',
        db_index=True,
        help_text="Type of coverage"
    )
    
    coverage_category = models.CharField(
        max_length=50, 
        choices=COVERAGE_CATEGORY_CHOICES,
        default='comprehensive',
        db_index=True,
        help_text="Category of coverage"
    )
    
    coverage_name = models.CharField(
        max_length=200,
        help_text="Name of the coverage"
    )
    
    coverage_description = models.TextField(
        help_text="Detailed description of the coverage"
    )
    
    coverage_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Coverage amount/limit"
    )
    
    deductible_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Deductible amount for this coverage"
    )
    
    coverage_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Coverage percentage (e.g., 100% for full coverage)"
    )
    
    is_included = models.BooleanField(
        default=True,
        help_text="Whether this coverage is included in the policy"
    )
    
    is_optional = models.BooleanField(
        default=False,
        help_text="Whether this coverage is optional"
    )
    
    premium_impact = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Additional premium for this coverage"
    )
    
    display_order = models.PositiveIntegerField(
        default=0,
        help_text="Order in which to display this coverage"
    )
    
    terms_conditions = models.TextField(
        blank=True,
        help_text="Specific terms and conditions for this coverage"
    )
    
    exclusions = models.TextField(
        blank=True,
        help_text="Exclusions for this coverage"
    )
    
    additional_info = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional information about the coverage"
    )
    
    class Meta:
        db_table = 'policy_coverages'
        ordering = ['coverage_type', 'display_order', 'coverage_name']
        indexes = [
            models.Index(fields=['policy', 'coverage_type']),
            models.Index(fields=['coverage_type', 'coverage_category']),
            models.Index(fields=['policy', 'is_included']),
            models.Index(fields=['display_order']),
        ]
        unique_together = ['policy', 'coverage_name', 'coverage_type']
    
    def __str__(self):
        return f"{self.policy.policy_number} - {self.coverage_name}"
    
    @property
    def policy_number(self):
        """Return the policy number for easy access"""
        return self.policy.policy_number if self.policy else None
    
    @property
    def customer_name(self):
        """Return the customer name for easy access"""
        return self.policy.customer.name if self.policy and self.policy.customer else None
