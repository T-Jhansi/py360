from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import BaseModel
from apps.policies.models import PolicyType

User = get_user_model()


class PolicyFeature(BaseModel):
    """Model to store policy features for different policies"""
    
    FEATURE_TYPE_CHOICES = [
        ('vehicle_insurance', 'Vehicle Insurance'),
        ('life_insurance', 'Life Insurance'),
        ('health_insurance', 'Health Insurance'),
        ('home_insurance', 'Home Insurance'),
        ('travel_insurance', 'Travel Insurance'),
        ('motor_insurance', 'Motor Insurance'),
        ('property_insurance', 'Property Insurance'),
        ('general', 'General'),
    ]
    
    policy_type = models.ForeignKey(
        PolicyType,
        on_delete=models.CASCADE,
        related_name='policy_features',
        help_text="Policy type this feature belongs to"
    )
    
    feature_type = models.CharField(
        max_length=50, 
        choices=FEATURE_TYPE_CHOICES,
        default='general',
        db_index=True,
        help_text="Type of insurance feature"
    )
    
    feature_name = models.CharField(
        max_length=200,
        help_text="Name of the policy feature"
    )
    
    feature_description = models.TextField(
        help_text="Detailed description of the feature"
    )
    
    feature_value = models.CharField(
        max_length=500,
        blank=True,
        help_text="Value or amount associated with the feature (if applicable)"
    )
    
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this feature is currently active"
    )
    
    is_mandatory = models.BooleanField(
        default=False,
        help_text="Whether this feature is mandatory for the policy"
    )
    
    display_order = models.PositiveIntegerField(
        default=0,
        help_text="Order in which to display this feature"
    )
    
    additional_info = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional information about the feature"
    )
    
    class Meta:
        db_table = 'policy_features'
        ordering = ['display_order', 'feature_name']
        indexes = [
            models.Index(fields=['policy_type', 'is_active']),
            models.Index(fields=['feature_type', 'is_active']),
            models.Index(fields=['policy_type', 'feature_type']),
            models.Index(fields=['display_order']),
        ]
        unique_together = ['policy_type', 'feature_name', 'feature_type']
    
    def __str__(self):
        return f"{self.policy_type.name} - {self.feature_name}"

    @property
    def policy_type_name(self):
        """Return the policy type name for easy access"""
        return self.policy_type.name if self.policy_type else None

    @property
    def policy_type_code(self):
        """Return the policy type code for easy access"""
        return self.policy_type.code if self.policy_type else None
