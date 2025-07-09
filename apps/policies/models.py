from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import BaseModel, TimestampedModel
from apps.customers.models import Customer
import uuid
from decimal import Decimal

User = get_user_model()

class PolicyType(BaseModel):
    """Types of insurance policies (Life, Health, Motor, etc.)"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    base_premium_rate = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    coverage_details = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'policy_types'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class Policy(BaseModel):
    """Main policy model"""
    POLICY_STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('pending', 'Pending'),
        ('suspended', 'Suspended'),
    ]
    
    policy_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='policies')
    policy_type = models.ForeignKey(PolicyType, on_delete=models.CASCADE, related_name='policies')
    
    # Policy Details
    start_date = models.DateField()
    end_date = models.DateField()
    premium_amount = models.DecimalField(max_digits=12, decimal_places=2)
    sum_assured = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, choices=POLICY_STATUS_CHOICES, default='pending')
    
    # Payment Details
    payment_frequency = models.CharField(max_length=20, choices=[
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('half_yearly', 'Half Yearly'),
        ('yearly', 'Yearly'),
    ], default='yearly')
    
    # Additional Details
    nominee_name = models.CharField(max_length=200, blank=True)
    nominee_relationship = models.CharField(max_length=100, blank=True)
    nominee_contact = models.CharField(max_length=20, blank=True)
    
    # Metadata
    policy_document = models.FileField(upload_to='policies/documents/', blank=True, null=True)
    terms_conditions = models.TextField(blank=True)
    special_conditions = models.TextField(blank=True)
    agent_name = models.CharField(max_length=200, blank=True)
    agent_code = models.CharField(max_length=50, blank=True)
    
    # System Fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_policies')
    last_modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='modified_policies')
    
    class Meta:
        db_table = 'policies'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['policy_number']),
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['end_date', 'status']),
        ]
    
    def __str__(self):
        return f"{self.policy_number} - {self.customer.full_name}"
    
    @property
    def is_due_for_renewal(self):
        """Check if policy is due for renewal (within 30 days)"""
        from datetime import date, timedelta
        return (self.end_date - date.today()).days <= 30
    
    @property
    def days_to_expiry(self):
        """Days remaining until policy expires"""
        from datetime import date
        return (self.end_date - date.today()).days

class PolicyRenewal(BaseModel):
    """Policy renewal tracking"""
    RENEWAL_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    
    policy = models.ForeignKey(Policy, on_delete=models.CASCADE, related_name='renewals')
    renewal_date = models.DateField()
    new_premium_amount = models.DecimalField(max_digits=12, decimal_places=2)
    new_sum_assured = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, choices=RENEWAL_STATUS_CHOICES, default='pending')
    
    # Renewal Details
    renewal_notice_sent = models.BooleanField(default=False)
    renewal_notice_date = models.DateTimeField(null=True, blank=True)
    customer_response = models.CharField(max_length=20, choices=[
        ('interested', 'Interested'),
        ('not_interested', 'Not Interested'),
        ('needs_time', 'Needs Time'),
        ('no_response', 'No Response'),
    ], default='no_response')
    
    # Communication Tracking
    contact_attempts = models.PositiveIntegerField(default=0)
    last_contact_date = models.DateTimeField(null=True, blank=True)
    contact_method = models.CharField(max_length=20, choices=[
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('whatsapp', 'WhatsApp'),
        ('sms', 'SMS'),
        ('in_person', 'In Person'),
    ], blank=True)
    
    notes = models.TextField(blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_renewals')
    
    class Meta:
        db_table = 'policy_renewals'
        ordering = ['-renewal_date']
        indexes = [
            models.Index(fields=['renewal_date', 'status']),
            models.Index(fields=['policy', 'status']),
        ]
    
    def __str__(self):
        return f"Renewal - {self.policy.policy_number} ({self.renewal_date})"

class PolicyClaim(BaseModel):
    """Insurance claims"""
    CLAIM_STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid'),
        ('closed', 'Closed'),
    ]
    
    CLAIM_TYPE_CHOICES = [
        ('death', 'Death Claim'),
        ('maturity', 'Maturity Claim'),
        ('surrender', 'Surrender'),
        ('partial_withdrawal', 'Partial Withdrawal'),
        ('accident', 'Accident'),
        ('medical', 'Medical'),
        ('disability', 'Disability'),
        ('other', 'Other'),
    ]
    
    claim_number = models.CharField(max_length=50, unique=True)
    policy = models.ForeignKey(Policy, on_delete=models.CASCADE, related_name='claims')
    claim_type = models.CharField(max_length=30, choices=CLAIM_TYPE_CHOICES)
    claim_amount = models.DecimalField(max_digits=15, decimal_places=2)
    approved_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Claim Details
    incident_date = models.DateField()
    claim_date = models.DateField()
    status = models.CharField(max_length=20, choices=CLAIM_STATUS_CHOICES, default='submitted')
    description = models.TextField()
    
    # Processing Details
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_claims')
    review_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Payment Details
    payment_date = models.DateField(null=True, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    
    class Meta:
        db_table = 'policy_claims'
        ordering = ['-claim_date']
        indexes = [
            models.Index(fields=['claim_number']),
            models.Index(fields=['policy', 'status']),
            models.Index(fields=['claim_date', 'status']),
        ]
    
    def __str__(self):
        return f"Claim {self.claim_number} - {self.policy.policy_number}"

class PolicyDocument(BaseModel):
    """Policy related documents"""
    DOCUMENT_TYPE_CHOICES = [
        ('policy_document', 'Policy Document'),
        ('renewal_notice', 'Renewal Notice'),
        ('claim_form', 'Claim Form'),
        ('medical_report', 'Medical Report'),
        ('identity_proof', 'Identity Proof'),
        ('address_proof', 'Address Proof'),
        ('income_proof', 'Income Proof'),
        ('other', 'Other'),
    ]
    
    policy = models.ForeignKey(Policy, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPE_CHOICES)
    document_name = models.CharField(max_length=200)
    file = models.FileField(upload_to='policies/documents/')
    file_size = models.PositiveIntegerField()
    mime_type = models.CharField(max_length=100)
    
    # Metadata
    description = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_documents')
    verified_at = models.DateTimeField(null=True, blank=True)
    
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_documents')
    
    class Meta:
        db_table = 'policy_documents'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.document_name} - {self.policy.policy_number}"

class PolicyBeneficiary(BaseModel):
    """Policy beneficiaries/nominees"""
    policy = models.ForeignKey(Policy, on_delete=models.CASCADE, related_name='beneficiaries')
    name = models.CharField(max_length=200)
    relationship = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    
    # Beneficiary Details
    date_of_birth = models.DateField(null=True, blank=True)
    id_type = models.CharField(max_length=50, blank=True)
    id_number = models.CharField(max_length=100, blank=True)
    percentage_share = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)
    
    is_primary = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'policy_beneficiaries'
        ordering = ['-is_primary', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.policy.policy_number}"

class PolicyPayment(BaseModel):
    """Policy payment tracking"""
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('net_banking', 'Net Banking'),
        ('upi', 'UPI'),
        ('wallet', 'Wallet'),
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    
    policy = models.ForeignKey(Policy, on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Payment Details
    transaction_id = models.CharField(max_length=100, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    
    # Period Details
    payment_for_period_start = models.DateField()
    payment_for_period_end = models.DateField()
    
    notes = models.TextField(blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        db_table = 'policy_payments'
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['policy', 'payment_date']),
            models.Index(fields=['transaction_id']),
        ]
    
    def __str__(self):
        return f"Payment {self.amount} - {self.policy.policy_number}"

class PolicyNote(BaseModel):
    """Internal notes for policies"""
    policy = models.ForeignKey(Policy, on_delete=models.CASCADE, related_name='notes')
    note = models.TextField()
    is_customer_visible = models.BooleanField(default=False)
    note_type = models.CharField(max_length=20, choices=[
        ('general', 'General'),
        ('follow_up', 'Follow Up'),
        ('complaint', 'Complaint'),
        ('renewal', 'Renewal'),
        ('claim', 'Claim'),
        ('payment', 'Payment'),
    ], default='general')
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'policy_notes'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Note - {self.policy.policy_number}" 