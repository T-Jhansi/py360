from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import BaseModel

User = get_user_model()


class Offer(BaseModel):
    """
    Model to store offers that are common for all customers
    Includes payment plans, discounts, product recommendations, etc.
    """
    
    OFFER_TYPE_CHOICES = [
        ('payment_option', 'Payment Option'),
        ('product', 'Product'),
        ('bundle', 'Bundle'),
        ('funding', 'Funding'),
        ('discount', 'Discount'),
        ('special_offer', 'Special Offer'),
    ]
    
    CURRENCY_CHOICES = [
        ('INR', 'Indian Rupee'),
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
    ]
    
    title = models.CharField(
        max_length=200,
        help_text="Offer title (e.g., 'EMI Payment Plan', 'Annual Payment')"
    )
    description = models.TextField(
        help_text="Detailed description of the offer"
    )
    offer_type = models.CharField(
        max_length=50,
        choices=OFFER_TYPE_CHOICES,
        help_text="Type of offer (payment_option, product, bundle, etc.)"
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Amount for payment plans (e.g., 1542 for EMI)"
    )
    discount = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Discount percentage or amount (e.g., '5%', '2% discount')"
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='INR',
        help_text="Currency for the amount"
    )
    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Interest rate for funding options (e.g., 3.5 for 3.5% p.a.)"
    )
    features = models.JSONField(
        default=list,
        blank=True,
        help_text="List of features/benefits (e.g., ['No additional charges', 'Flexible payment schedule'])"
    )
    extra_info = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional information as JSON (e.g., terms, conditions, special notes)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this offer is currently active"
    )
    display_order = models.PositiveIntegerField(
        default=0,
        help_text="Order for displaying offers (lower numbers appear first)"
    )
    icon = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Icon name or class for frontend display"
    )
    color_scheme = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Color scheme for frontend display (e.g., 'blue', 'green', 'orange')"
    )
    terms_and_conditions = models.TextField(
        null=True,
        blank=True,
        help_text="Terms and conditions for this offer"
    )
    start_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this offer becomes active"
    )
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this offer expires"
    )
    
    class Meta:
        db_table = 'offers'
        ordering = ['display_order', 'created_at']
        indexes = [
            models.Index(fields=['offer_type', 'is_active']),
            models.Index(fields=['is_active', 'display_order']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_offer_type_display()})"
    
    @property
    def is_currently_active(self):
        """Check if offer is currently active based on dates and status"""
        from django.utils import timezone
        now = timezone.now()
        
        if not self.is_active:
            return False
            
        if self.start_date and now < self.start_date:
            return False
            
        if self.end_date and now > self.end_date:
            return False
            
        return True
    
    @property
    def formatted_amount(self):
        """Return formatted amount with currency"""
        if not self.amount:
            return None
        return f"₹{self.amount:,.2f}" if self.currency == 'INR' else f"{self.currency} {self.amount:,.2f}"
    
    @property
    def formatted_interest_rate(self):
        """Return formatted interest rate"""
        if not self.interest_rate:
            return None
        return f"{self.interest_rate}% p.a."