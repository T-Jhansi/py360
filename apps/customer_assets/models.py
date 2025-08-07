from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import BaseModel
from apps.customers.models import Customer


class CustomerAssets(BaseModel):
    RESIDENCE_TYPE_CHOICES = [
        ('apartment', 'Apartment'),
        ('house', 'House'),
        ('villa', 'Villa'),
        ('bungalow', 'Bungalow'),
        ('flat', 'Flat'),
        ('penthouse', 'Penthouse'),
        ('studio', 'Studio'),
        ('other', 'Other'),
    ]
    
    RESIDENCE_STATUS_CHOICES = [
        ('owned', 'Owned'),
        ('rented', 'Rented'),
        ('leased', 'Leased'),
        ('family_owned', 'Family Owned'),
        ('company_provided', 'Company Provided'),
        ('other', 'Other'),
    ]
    
    RESIDENCE_RATING_CHOICES = [
        ('excellent', 'Excellent'),
        ('very_good', 'Very Good'),
        ('good', 'Good'),
        ('average', 'Average'),
        ('below_average', 'Below Average'),
        ('poor', 'Poor'),
    ]
    
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='assets',
        help_text="Customer who owns these assets"
    )
    
    residence_type = models.CharField(
        max_length=50,
        choices=RESIDENCE_TYPE_CHOICES,
        blank=True,
        help_text="Type of residence"
    )
    
    residence_status = models.CharField(
        max_length=50,
        choices=RESIDENCE_STATUS_CHOICES,
        blank=True,
        help_text="Ownership status of residence"
    )
    
    residence_location = models.CharField(
        max_length=200,
        blank=True,
        help_text="Location/address of residence"
    )
    
    residence_rating = models.CharField(
        max_length=20,
        choices=RESIDENCE_RATING_CHOICES,
        blank=True,
        help_text="Quality/condition rating of residence"
    )
    
    class Meta:
        db_table = 'customer_assets'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer']),
            models.Index(fields=['residence_type']),
            models.Index(fields=['residence_status']),
            models.Index(fields=['residence_rating']),
        ]
    
    def __str__(self):
        return f"Assets - {self.customer.full_name} ({self.residence_type})"
    
    @property
    def residence_summary(self):
        """Return a summary of residence information"""
        parts = []
        if self.residence_type:
            parts.append(self.get_residence_type_display())
        if self.residence_status:
            parts.append(self.get_residence_status_display())
        if self.residence_location:
            parts.append(self.residence_location)
        return " - ".join(parts) if parts else "No residence information"
    
    @property
    def asset_score(self):
        score = 0
        
        type_scores = {
            'penthouse': 10,
            'villa': 9,
            'bungalow': 8,
            'house': 7,
            'apartment': 6,
            'flat': 5,
            'studio': 4,
            'other': 3,
        }
        score += type_scores.get(self.residence_type, 0)
        
        status_scores = {
            'owned': 10,
            'family_owned': 8,
            'leased': 6,
            'rented': 4,
            'company_provided': 5,
            'other': 2,
        }
        score += status_scores.get(self.residence_status, 0)
        
        rating_scores = {
            'excellent': 10,
            'very_good': 8,
            'good': 6,
            'average': 4,
            'below_average': 2,
            'poor': 1,
        }
        score += rating_scores.get(self.residence_rating, 0)
        
        return min(score, 30) 
