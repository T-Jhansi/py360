"""
Serializers for Outstanding Amounts functionality
"""

from rest_framework import serializers
from decimal import Decimal


class OutstandingInstallmentSerializer(serializers.Serializer):
    """
    Serializer for individual outstanding installment
    """
    id = serializers.IntegerField()
    period = serializers.CharField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    due_date = serializers.DateField()
    days_overdue = serializers.IntegerField()
    status = serializers.CharField()
    description = serializers.CharField()


class OutstandingAmountsSummarySerializer(serializers.Serializer):
    """
    Serializer for outstanding amounts summary
    """
    total_outstanding = serializers.DecimalField(max_digits=12, decimal_places=2)
    oldest_due_date = serializers.DateField(allow_null=True)
    latest_due_date = serializers.DateField(allow_null=True)
    average_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    pending_count = serializers.IntegerField()
    overdue_count = serializers.IntegerField()
    installments = OutstandingInstallmentSerializer(many=True)


class PaymentInitiationSerializer(serializers.Serializer):
    """
    Serializer for payment initiation request
    """
    installment_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        help_text="List of installment IDs to pay. If empty, all outstanding installments will be paid."
    )
    payment_mode = serializers.ChoiceField(
        choices=[
            ('credit_card', 'Credit Card'),
            ('debit_card', 'Debit Card'),
            ('net_banking', 'Net Banking'),
            ('upi', 'UPI'),
            ('wallet', 'Digital Wallet'),
            ('bank_transfer', 'Bank Transfer'),
            ('cheque', 'Cheque'),
            ('cash', 'Cash'),
            ('emi', 'EMI'),
            ('auto_debit', 'Auto Debit'),
        ],
        default='upi',
        help_text="Payment mode for the transaction"
    )
    payment_notes = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        help_text="Additional notes for the payment"
    )


class PaymentPlanSetupSerializer(serializers.Serializer):
    """
    Serializer for payment plan setup request
    """
    installment_count = serializers.IntegerField(
        min_value=2,
        max_value=12,
        default=3,
        help_text="Number of installments (2-12)"
    )
    start_date = serializers.DateField(
        help_text="Start date for the payment plan"
    )
    payment_frequency = serializers.ChoiceField(
        choices=[
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
        ],
        default='monthly',
        help_text="Frequency of payments"
    )
    payment_method = serializers.ChoiceField(
        choices=[
            ('credit_card', 'Credit Card'),
            ('debit_card', 'Debit Card'),
            ('net_banking', 'Net Banking'),
            ('upi', 'UPI'),
            ('wallet', 'Digital Wallet'),
            ('bank_transfer', 'Bank Transfer'),
            ('cheque', 'Cheque'),
            ('cash', 'Cash'),
            ('emi', 'EMI'),
            ('auto_debit', 'Auto Debit'),
            ('standing_instruction', 'Standing Instruction'),
            ('nach', 'NACH'),
            ('enach', 'E-NACH'),
        ],
        default='auto_debit',
        help_text="Payment method for the plan"
    )
    auto_payment_enabled = serializers.BooleanField(
        default=True,
        help_text="Whether to enable automatic payments"
    )
    plan_notes = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        help_text="Additional notes for the payment plan"
    )


class PaymentResponseSerializer(serializers.Serializer):
    """
    Serializer for payment initiation response
    """
    success = serializers.BooleanField()
    message = serializers.CharField()
    payment_id = serializers.IntegerField(required=False, allow_null=True)
    transaction_id = serializers.CharField(required=False, allow_null=True)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)


class PaymentPlanResponseSerializer(serializers.Serializer):
    """
    Serializer for payment plan setup response
    """
    success = serializers.BooleanField()
    message = serializers.CharField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    installment_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    installment_count = serializers.IntegerField(required=False, allow_null=True)
    payment_frequency = serializers.CharField(required=False, allow_null=True)
    schedules_created = serializers.IntegerField(required=False, allow_null=True)
