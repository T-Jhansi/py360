"""
Other Insurance Policies models for the Intelipro Insurance Policy Renewal System.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from apps.core.models import BaseModel
from apps.customers.models import Customer
from apps.policies.models import PolicyType


class OtherInsurancePolicy(BaseModel):
    """
    Other insurance policies that customers have with different companies.
    This helps in understanding customer's complete insurance portfolio.
    """
    
    POLICY_STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('lapsed', 'Lapsed'),
        ('matured', 'Matured'),
        ('surrendered', 'Surrendered'),
        ('pending', 'Pending'),
        ('unknown', 'Unknown'),
    ]
    
    PAYMENT_MODE_CHOICES = [
        ('annual', 'Annual'),
        ('semi_annual', 'Semi-Annual'),
        ('quarterly', 'Quarterly'),
        ('monthly', 'Monthly'),
        ('single_premium', 'Single Premium'),
        ('unknown', 'Unknown'),
    ]
    
    CHANNEL_CHOICES = [
        ('agent', 'Agent'),
        ('broker', 'Broker'),
        ('bank', 'Bank Channel'),
        ('online', 'Online Portal'),
        ('direct', 'Direct from Company'),
        ('corporate', 'Corporate Tie-up'),
        ('other', 'Other'),
        ('unknown', 'Unknown'),
    ]
    
    # Foreign Keys
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='other_insurance_policies',
        help_text="Customer who owns this policy"
    )
    
    policy_type = models.ForeignKey(
        PolicyType,
        on_delete=models.CASCADE,
        related_name='other_insurance_policies',
        help_text="Type of insurance policy (fetched from policies table)"
    )
    
    # Policy Basic Information
    policy_number = models.CharField(
        max_length=100,
        help_text="Policy number from other insurance company"
    )
    
    insurance_company = models.CharField(
        max_length=200,
        help_text="Name of the insurance company"
    )
    
    policy_status = models.CharField(
        max_length=20,
        choices=POLICY_STATUS_CHOICES,
        default='active',
        help_text="Current status of the policy"
    )
    
    # Policy Dates
    start_date = models.DateField(
        help_text="Policy start date"
    )
    
    end_date = models.DateField(
        help_text="Policy end/maturity date"
    )
    
    next_renewal_date = models.DateField(
        blank=True,
        null=True,
        help_text="Next renewal date if applicable"
    )
    
    # Financial Information
    premium_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Premium amount"
    )
    
    sum_assured = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Sum assured/coverage amount"
    )
    
    payment_mode = models.CharField(
        max_length=20,
        choices=PAYMENT_MODE_CHOICES,
        default='annual',
        help_text="Premium payment frequency"
    )
    
    # Policy Details
    nominee_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Nominee name"
    )
    
    nominee_relationship = models.CharField(
        max_length=100,
        blank=True,
        help_text="Relationship with nominee"
    )
    
    agent_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Agent/advisor name"
    )
    
    agent_contact = models.CharField(
        max_length=20,
        blank=True,
        help_text="Agent contact number"
    )
    
    channel = models.CharField(
        max_length=20,
        choices=CHANNEL_CHOICES,
        default='unknown',
        help_text="Channel through which policy was purchased"
    )
    
    # Additional Information
    policy_features = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional policy features and benefits"
    )
    
    riders = models.JSONField(
        default=list,
        blank=True,
        help_text="List of riders attached to the policy"
    )
    
    exclusions = models.TextField(
        blank=True,
        help_text="Policy exclusions"
    )
    
    special_conditions = models.TextField(
        blank=True,
        help_text="Special conditions or terms"
    )
    
    # Satisfaction and Experience
    satisfaction_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        blank=True,
        null=True,
        help_text="Customer satisfaction rating (1-5)"
    )
    
    claim_experience = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent'),
            ('good', 'Good'),
            ('average', 'Average'),
            ('poor', 'Poor'),
            ('very_poor', 'Very Poor'),
            ('no_claims', 'No Claims Made'),
        ],
        blank=True,
        help_text="Customer's claim experience"
    )
    
    # Renewal Information
    is_renewal_interested = models.BooleanField(
        default=True,
        help_text="Whether customer is interested in renewing"
    )
    
    renewal_concerns = models.TextField(
        blank=True,
        help_text="Customer concerns about renewal"
    )
    
    competitor_advantages = models.TextField(
        blank=True,
        help_text="Advantages this policy has over our offerings"
    )
    
    switching_potential = models.CharField(
        max_length=20,
        choices=[
            ('high', 'High'),
            ('medium', 'Medium'),
            ('low', 'Low'),
            ('none', 'None'),
        ],
        default='medium',
        help_text="Potential for customer to switch to our company"
    )
    
    # Internal Notes
    notes = models.TextField(
        blank=True,
        help_text="Internal notes about this policy"
    )
    
    last_updated_by_customer = models.DateField(
        blank=True,
        null=True,
        help_text="When customer last updated this information"
    )
    
    verification_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending Verification'),
            ('verified', 'Verified'),
            ('rejected', 'Rejected'),
            ('needs_update', 'Needs Update'),
        ],
        default='pending',
        help_text="Verification status of the policy information"
    )
    
    class Meta:
        db_table = 'other_insurance_policies'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer']),
            models.Index(fields=['policy_type']),
            models.Index(fields=['insurance_company']),
            models.Index(fields=['policy_status']),
            models.Index(fields=['end_date']),
            models.Index(fields=['next_renewal_date']),
            models.Index(fields=['switching_potential']),
            models.Index(fields=['verification_status']),
        ]
        unique_together = ['customer', 'policy_number', 'insurance_company']
    
    def __str__(self):
        return f"{self.customer.full_name} - {self.policy_type.name} - {self.insurance_company}"
    
    @property
    def policy_summary(self):
        """Return a summary of the policy"""
        parts = []
        parts.append(f"{self.policy_type.name}")
        parts.append(f"{self.insurance_company}")
        parts.append(f"₹{self.sum_assured:,.2f}")
        if self.policy_status:
            parts.append(f"({self.get_policy_status_display()})")
        return " - ".join(parts)
    
    @property
    def annual_premium(self):
        """Calculate annual premium based on payment mode"""
        if self.payment_mode == 'monthly':
            return self.premium_amount * 12
        elif self.payment_mode == 'quarterly':
            return self.premium_amount * 4
        elif self.payment_mode == 'semi_annual':
            return self.premium_amount * 2
        else:  # annual or single_premium
            return self.premium_amount
    
    @property
    def is_expiring_soon(self):
        """Check if policy is expiring within 90 days"""
        from datetime import date, timedelta
        if self.end_date:
            return self.end_date <= date.today() + timedelta(days=90)
        return False
    
    @property
    def days_to_expiry(self):
        """Get number of days until policy expires"""
        from datetime import date
        if self.end_date:
            delta = self.end_date - date.today()
            return delta.days
        return None
    
    @property
    def policy_age_years(self):
        """Calculate policy age in years"""
        from datetime import date
        if self.start_date:
            delta = date.today() - self.start_date
            return round(delta.days / 365.25, 1)
        return None
    
    @property
    def competitive_analysis_score(self):
        """Calculate a score for competitive analysis (0-100)"""
        score = 0
        
        # Base score for having the information
        score += 20
        
        # Satisfaction rating (20 points)
        if self.satisfaction_rating:
            score += (self.satisfaction_rating * 4)  # 4-20 points
        
        # Claim experience (20 points)
        claim_scores = {
            'excellent': 20,
            'good': 15,
            'average': 10,
            'poor': 5,
            'very_poor': 0,
            'no_claims': 12,  # Neutral score
        }
        score += claim_scores.get(self.claim_experience, 0)
        
        # Switching potential (20 points)
        switch_scores = {
            'high': 20,
            'medium': 12,
            'low': 5,
            'none': 0,
        }
        score += switch_scores.get(self.switching_potential, 0)
        
        # Renewal interest (20 points)
        if self.is_renewal_interested:
            score += 20
        else:
            score += 5  # Still some potential
        
        return min(score, 100)
    
    @property
    def risk_indicators(self):
        """Identify risk indicators for customer retention"""
        risks = []
        
        if self.satisfaction_rating and self.satisfaction_rating <= 2:
            risks.append("Low satisfaction rating")
        
        if self.claim_experience in ['poor', 'very_poor']:
            risks.append("Poor claim experience")
        
        if not self.is_renewal_interested:
            risks.append("Not interested in renewal")
        
        if self.switching_potential in ['high', 'medium']:
            risks.append("High switching potential")
        
        if self.is_expiring_soon:
            risks.append("Policy expiring soon")
        
        return risks
