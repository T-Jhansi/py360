from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.customers.models import Customer
from apps.customers_files.models import CustomerFile

User = get_user_model()


class CustomerDocument(models.Model):
    """Model to store customer document information"""
    
    DOCUMENT_TYPE_CHOICES = [
        ('id_proof', 'ID Proof'),
        ('address_proof', 'Address Proof'),
        ('income_proof', 'Income Proof'),
        ('business_registration', 'Business Registration'),
        ('tax_document', 'Tax Document'),
        ('bank_statement', 'Bank Statement'),
        ('medical_report', 'Medical Report'),
        ('photo', 'Photograph'),
        ('signature', 'Signature'),
        ('authorization', 'Authorization Letter'),
        ('passport', 'Passport'),
        ('driving_license', 'Driving License'),
        ('voter_id', 'Voter ID'),
        ('pan_card', 'PAN Card'),
        ('aadhar_card', 'Aadhar Card'),
        ('utility_bill', 'Utility Bill'),
        ('rental_agreement', 'Rental Agreement'),
        ('property_document', 'Property Document'),
        ('salary_slip', 'Salary Slip'),
        ('form_16', 'Form 16'),
        ('itr', 'Income Tax Return'),
        ('other', 'Other'),
    ]
    
    # Basic document information
    document_type = models.CharField(
        max_length=30, 
        choices=DOCUMENT_TYPE_CHOICES, 
        db_index=True,
        help_text="Type of document"
    )
    document_number = models.CharField(
        max_length=100, 
        blank=True,
        help_text="Document number (e.g., passport number, license number)"
    )
    
    # Verification status
    is_verified = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether the document has been verified"
    )
    verified_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Timestamp when document was verified"
    )
    verification_notes = models.TextField(
        blank=True,
        help_text="Notes from verification process"
    )
    
    # Document dates
    issue_date = models.DateField(
        null=True, 
        blank=True,
        help_text="Date when document was issued"
    )
    expiry_date = models.DateField(
        null=True, 
        blank=True,
        db_index=True,
        help_text="Date when document expires"
    )
    
    # Issuing authority
    issuing_authority = models.CharField(
        max_length=200, 
        blank=True,
        help_text="Authority that issued the document"
    )
    
    # Additional notes
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about the document"
    )
    
    # Foreign key relationships
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='documents_new',
        help_text="Customer this document belongs to"
    )

    file = models.ForeignKey(
        CustomerFile,
        on_delete=models.CASCADE,
        related_name='customer_documents_new',
        help_text="Customer file for this document"
    )

    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_customer_documents_new',
        help_text="User who verified this document"
    )

    # Timestamp fields
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    # Soft delete fields
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # User tracking fields
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customer_documents_new_created_objects'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customer_documents_new_updated_objects'
    )
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customer_documents_new_deleted_objects'
    )
    
    class Meta:
        db_table = 'customers_documents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer', 'document_type']),
            models.Index(fields=['document_type', 'is_verified']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['expiry_date']),
            models.Index(fields=['verified_at']),
            models.Index(fields=['customer', 'is_verified']),
        ]
        
    def __str__(self):
        return f"{self.customer} - {self.get_document_type_display()}"

    def delete(self, using=None, keep_parents=False, user=None):
        """Soft delete the object"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if user:
            self.deleted_by = user
        self.save(using=using)

    def hard_delete(self, using=None, keep_parents=False):
        """Permanently delete the object"""
        super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        """Restore a soft-deleted object"""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save()
    
    def is_expired(self):
        """Check if document is expired"""
        if self.expiry_date:
            return timezone.now().date() > self.expiry_date
        return False
    
    def is_expiring_soon(self, days=30):
        """Check if document is expiring within specified days"""
        if self.expiry_date:
            from datetime import timedelta
            warning_date = timezone.now().date() + timedelta(days=days)
            return self.expiry_date <= warning_date
        return False
    
    @property
    def verification_status(self):
        """Return human-readable verification status"""
        if self.is_verified:
            return "Verified"
        return "Pending Verification"
    
    @property
    def expiry_status(self):
        """Return human-readable expiry status"""
        if not self.expiry_date:
            return "No Expiry"
        
        if self.is_expired():
            return "Expired"
        elif self.is_expiring_soon():
            return "Expiring Soon"
        else:
            return "Valid"
