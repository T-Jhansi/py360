"""
Views for Customer Payments app.
"""

from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum, Count, Avg, Max, Min
from django.utils import timezone
from decimal import Decimal
from apps.core.pagination import StandardResultsSetPagination
from .models import CustomerPayment
from .serializers import (
    CustomerPaymentSerializer,
    CustomerPaymentCreateSerializer,
    CustomerPaymentUpdateSerializer,
    CustomerPaymentListSerializer,
    CustomerPaymentSummarySerializer,
    PaymentRefundSerializer,
    PaymentStatusUpdateSerializer
)



class CustomerPaymentListCreateView(generics.ListCreateAPIView):
    """
    List all customer payments or create a new one.
    """
    queryset = CustomerPayment.objects.filter(is_deleted=False)
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CustomerPaymentCreateSerializer
        return CustomerPaymentListSerializer
    
    def get_queryset(self):
        queryset = CustomerPayment.objects.filter(is_deleted=False)
        
        # Filter by renewal case
        renewal_case_id = self.request.query_params.get('renewal_case_id')
        if renewal_case_id:
            queryset = queryset.filter(renewal_case_id=renewal_case_id)
        
        # Filter by customer
        customer_id = self.request.query_params.get('customer_id')
        if customer_id:
            queryset = queryset.filter(renewal_case__customer_id=customer_id)
        
        # Filter by payment status
        payment_status = self.request.query_params.get('payment_status')
        if payment_status:
            queryset = queryset.filter(payment_status=payment_status)
        
        # Filter by payment mode
        payment_mode = self.request.query_params.get('payment_mode')
        if payment_mode:
            queryset = queryset.filter(payment_mode=payment_mode)
        
        # Filter by payment gateway
        payment_gateway = self.request.query_params.get('payment_gateway')
        if payment_gateway:
            queryset = queryset.filter(payment_gateway=payment_gateway)
        
        # Filter by currency
        currency = self.request.query_params.get('currency')
        if currency:
            queryset = queryset.filter(currency=currency)
        
        # Filter by auto payment
        is_auto_payment = self.request.query_params.get('is_auto_payment')
        if is_auto_payment is not None:
            queryset = queryset.filter(is_auto_payment=is_auto_payment.lower() == 'true')
        
        # Filter by amount range
        min_amount = self.request.query_params.get('min_amount')
        max_amount = self.request.query_params.get('max_amount')
        if min_amount:
            queryset = queryset.filter(payment_amount__gte=min_amount)
        if max_amount:
            queryset = queryset.filter(payment_amount__lte=max_amount)
        
        # Filter by payment date range
        payment_from = self.request.query_params.get('payment_from')
        payment_to = self.request.query_params.get('payment_to')
        if payment_from:
            queryset = queryset.filter(payment_date__gte=payment_from)
        if payment_to:
            queryset = queryset.filter(payment_date__lte=payment_to)
        
        # Filter by due date range
        due_from = self.request.query_params.get('due_from')
        due_to = self.request.query_params.get('due_to')
        if due_from:
            queryset = queryset.filter(due_date__gte=due_from)
        if due_to:
            queryset = queryset.filter(due_date__lte=due_to)
        
        # Filter overdue payments
        overdue_only = self.request.query_params.get('overdue_only')
        if overdue_only and overdue_only.lower() == 'true':
            today = timezone.now().date()
            queryset = queryset.filter(
                due_date__lt=today,
                payment_status__in=['pending', 'failed']
            )
        
        # Filter successful payments
        successful_only = self.request.query_params.get('successful_only')
        if successful_only and successful_only.lower() == 'true':
            queryset = queryset.filter(payment_status='completed')
        
        # Filter failed payments
        failed_only = self.request.query_params.get('failed_only')
        if failed_only and failed_only.lower() == 'true':
            queryset = queryset.filter(payment_status__in=['failed', 'cancelled'])
        
        # Filter pending payments
        pending_only = self.request.query_params.get('pending_only')
        if pending_only and pending_only.lower() == 'true':
            queryset = queryset.filter(payment_status__in=['pending', 'processing'])
        
        # Filter refunded payments
        refunded_only = self.request.query_params.get('refunded_only')
        if refunded_only and refunded_only.lower() == 'true':
            queryset = queryset.filter(
                Q(payment_status='refunded') | Q(refund_amount__gt=0)
            )
        
        # Search by transaction ID, reference number, receipt number, or customer details
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(transaction_id__icontains=search) |
                Q(reference_number__icontains=search) |
                Q(receipt_number__icontains=search) |
                Q(renewal_case__customer__first_name__icontains=search) |
                Q(renewal_case__customer__last_name__icontains=search) |
                Q(renewal_case__customer__customer_code__icontains=search) |
                Q(renewal_case__case_number__icontains=search) |
                Q(renewal_case__policy__policy_number__icontains=search)
            )
        
        return queryset.select_related(
            'renewal_case',
            'renewal_case__customer',
            'renewal_case__policy'
        ).order_by('-payment_date', '-created_at')
    
    def perform_create(self, serializer):
        """Create customer payment"""
        serializer.save(created_by=self.request.user)


class CustomerPaymentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete customer payment.
    """
    queryset = CustomerPayment.objects.filter(is_deleted=False)
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return CustomerPaymentUpdateSerializer
        return CustomerPaymentSerializer
    
    def perform_update(self, serializer):
        """Update customer payment"""
        serializer.save(updated_by=self.request.user)
    
    def perform_destroy(self, instance):
        """Soft delete the customer payment"""
        instance.delete(user=self.request.user)


@api_view(['GET'])
def customer_payments_by_renewal_case(request, renewal_case_id):
    """
    Get all payments for a specific renewal case.
    """
    payments = CustomerPayment.objects.filter(
        renewal_case_id=renewal_case_id,
        is_deleted=False
    )
    serializer = CustomerPaymentListSerializer(payments, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def customer_payments_by_customer(request, customer_id):
    """
    Get all payments for a specific customer.
    """
    payments = CustomerPayment.objects.filter(
        renewal_case__customer_id=customer_id,
        is_deleted=False
    )
    serializer = CustomerPaymentListSerializer(payments, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def process_payment_refund(request, payment_id):
    """
    Process refund for a specific payment.
    """
    payment = get_object_or_404(CustomerPayment, id=payment_id, is_deleted=False)
    
    serializer = PaymentRefundSerializer(
        data=request.data,
        context={'payment': payment}
    )
    
    if serializer.is_valid():
        refund_amount = serializer.validated_data['refund_amount']
        refund_reference = serializer.validated_data.get('refund_reference', '')
        
        try:
            payment.process_refund(refund_amount, refund_reference)
            return Response({
                'message': 'Refund processed successfully',
                'payment_id': payment.id,
                'refund_amount': refund_amount,
                'refund_reference': refund_reference,
                'new_status': payment.payment_status
            })
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def update_payment_status(request, payment_id):
    """
    Update payment status with additional details.
    """
    payment = get_object_or_404(CustomerPayment, id=payment_id, is_deleted=False)
    
    serializer = PaymentStatusUpdateSerializer(data=request.data)
    
    if serializer.is_valid():
        payment_status = serializer.validated_data['payment_status']
        
        # Update payment fields
        payment.payment_status = payment_status
        
        if 'transaction_id' in serializer.validated_data:
            payment.transaction_id = serializer.validated_data['transaction_id']
        
        if 'reference_number' in serializer.validated_data:
            payment.reference_number = serializer.validated_data['reference_number']
        
        if 'failure_reason' in serializer.validated_data:
            payment.failure_reason = serializer.validated_data['failure_reason']
        
        if 'failure_code' in serializer.validated_data:
            payment.failure_code = serializer.validated_data['failure_code']
        
        if 'gateway_response' in serializer.validated_data:
            payment.gateway_response = serializer.validated_data['gateway_response']
        
        payment.updated_by = request.user
        payment.save()
        
        return Response({
            'message': 'Payment status updated successfully',
            'payment_id': payment.id,
            'new_status': payment.payment_status,
            'transaction_id': payment.transaction_id,
            'reference_number': payment.reference_number
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def payment_statistics(request):
    """
    Get statistics about customer payments.
    """
    payments = CustomerPayment.objects.filter(is_deleted=False)
    
    # Payment status distribution
    status_distribution = {}
    for choice in CustomerPayment.PAYMENT_STATUS_CHOICES:
        status_key = choice[0]
        count = payments.filter(payment_status=status_key).count()
        status_distribution[status_key] = count
    
    # Payment mode distribution
    mode_distribution = {}
    for choice in CustomerPayment.PAYMENT_MODE_CHOICES:
        mode_key = choice[0]
        count = payments.filter(payment_mode=mode_key).count()
        mode_distribution[mode_key] = count
    
    # Payment gateway distribution
    gateway_distribution = {}
    gateway_counts = payments.values('payment_gateway').annotate(
        count=Count('id')
    ).order_by('-count')
    for item in gateway_counts:
        gateway_distribution[item['payment_gateway'] or 'Unknown'] = item['count']
    
    # Currency distribution
    currency_distribution = {}
    currency_counts = payments.values('currency').annotate(
        count=Count('id')
    ).order_by('-count')
    for item in currency_counts:
        currency_distribution[item['currency']] = item['count']
    
    # Amount ranges
    amount_ranges = {
        'under_1000': payments.filter(payment_amount__lt=1000).count(),
        '1000_to_5000': payments.filter(payment_amount__gte=1000, payment_amount__lt=5000).count(),
        '5000_to_10000': payments.filter(payment_amount__gte=5000, payment_amount__lt=10000).count(),
        '10000_to_50000': payments.filter(payment_amount__gte=10000, payment_amount__lt=50000).count(),
        '50000_to_100000': payments.filter(payment_amount__gte=50000, payment_amount__lt=100000).count(),
        'above_100000': payments.filter(payment_amount__gte=100000).count(),
    }
    
    # Time-based analysis
    today = timezone.now().date()
    overdue_payments = payments.filter(
        due_date__lt=today,
        payment_status__in=['pending', 'failed']
    ).count()
    
    auto_payments = payments.filter(is_auto_payment=True).count()
    manual_payments = payments.filter(is_auto_payment=False).count()
    
    # Aggregate statistics
    aggregates = payments.aggregate(
        total_payments=Count('id'),
        total_amount=Sum('payment_amount'),
        avg_amount=Avg('payment_amount'),
        max_amount=Max('payment_amount'),
        min_amount=Min('payment_amount'),
        total_refunds=Sum('refund_amount'),
        total_fees=Sum('processing_fee'),
        total_taxes=Sum('tax_amount'),
        total_discounts=Sum('discount_amount')
    )
    
    return Response({
        'total_payments': aggregates['total_payments'],
        'total_amount': aggregates['total_amount'],
        'average_amount': aggregates['avg_amount'],
        'max_amount': aggregates['max_amount'],
        'min_amount': aggregates['min_amount'],
        'total_refunds': aggregates['total_refunds'],
        'total_fees': aggregates['total_fees'],
        'total_taxes': aggregates['total_taxes'],
        'total_discounts': aggregates['total_discounts'],
        'overdue_payments_count': overdue_payments,
        'auto_payments_count': auto_payments,
        'manual_payments_count': manual_payments,
        'payment_status_distribution': status_distribution,
        'payment_mode_distribution': mode_distribution,
        'payment_gateway_distribution': gateway_distribution,
        'currency_distribution': currency_distribution,
        'amount_distribution': amount_ranges,
    })


@api_view(['GET'])
def payment_summary(request):
    """
    Get summary of all customer payments for analytics.
    """
    payments = CustomerPayment.objects.filter(is_deleted=False)
    serializer = CustomerPaymentSummarySerializer(payments, many=True)
    return Response(serializer.data)
