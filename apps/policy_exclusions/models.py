from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import BaseModel
from apps.policies.models import Policy

User = get_user_model()


class PolicyExclusion(BaseModel):
    """Model to store policy exclusions"""
    
    EXCLUSION_TYPE_CHOICES = [
        ('not_covered', 'Not Covered'),
        ('conditions_apply', 'Conditions Apply'),
        ('partial_coverage', 'Partial Coverage'),
        ('waiting_period', 'Waiting Period'),
        ('geographical_limit', 'Geographical Limit'),
        ('age_limit', 'Age Limit'),
        ('pre_existing_condition', 'Pre-existing Condition'),
        ('activity_exclusion', 'Activity Exclusion'),
        ('other', 'Other'),
    ]
    
    policy = models.ForeignKey(
        Policy,
        on_delete=models.CASCADE,
        related_name='exclusions',
        help_text="Links this exclusion to a specific policy"
    )
    
    exclusion_type = models.CharField(
        max_length=50,
        choices=EXCLUSION_TYPE_CHOICES,
        default='not_covered',
        db_index=True,
        help_text="Type of exclusion — e.g., not_covered or conditions_apply"
    )
    
    description = models.TextField(
        blank=True,
        help_text="The actual exclusion text"
    )
    
    class Meta:
        db_table = 'policy_exclusions'
        ordering = ['policy', 'exclusion_type', 'id']
        indexes = [
            models.Index(fields=['policy', 'exclusion_type']),
            models.Index(fields=['exclusion_type']),
            models.Index(fields=['policy']),
        ]
    
    def __str__(self):
        return f"{self.policy.policy_number} - {self.exclusion_type}: {self.description[:50]}..."
    
    @property
    def policy_number(self):
        """Return the policy number for easy access"""
        return self.policy.policy_number if self.policy else None
    
    @property
    def policy_type_name(self):
        """Return the policy type name for easy access"""
        return self.policy.policy_type.name if self.policy and self.policy.policy_type else None
