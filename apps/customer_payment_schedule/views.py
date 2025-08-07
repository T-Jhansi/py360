"""
Views for Customer Payment Schedule app.
"""

from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum, Count, Avg, Max, Min
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from apps.core.pagination import StandardResultsSetPagination
from .models import PaymentSchedule
from .serializers import (
    PaymentScheduleSerializer,
    PaymentScheduleCreateSerializer,
    PaymentScheduleUpdateSerializer,
    PaymentScheduleListSerializer,
    PaymentScheduleSummarySerializer,
    PaymentProcessingSerializer,
    PaymentRescheduleSerializer,
    PaymentFailureSerializer,
    AutoPaymentSerializer,
    BulkScheduleCreateSerializer
)


class PaymentScheduleListCreateView(generics.ListCreateAPIView):
    """
    List all payment schedules or create a new one.
    """
    queryset = PaymentSchedule.objects.filter(is_deleted=False)
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PaymentScheduleCreateSerializer
        return PaymentScheduleListSerializer
    
    def get_queryset(self):
        queryset = PaymentSchedule.objects.filter(is_deleted=False)
        
        # Filter by renewal case
        renewal_case_id = self.request.query_params.get('renewal_case_id')
        if renewal_case_id:
            queryset = queryset.filter(renewal_case_id=renewal_case_id)
        
        # Filter by customer
        customer_id = self.request.query_params.get('customer_id')
        if customer_id:
            queryset = queryset.filter(renewal_case__customer_id=customer_id)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by payment method
        payment_method = self.request.query_params.get('payment_method')
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)
        
        # Filter by auto payment
        auto_payment = self.request.query_params.get('auto_payment')
        if auto_payment is not None:
            queryset = queryset.filter(auto_payment_enabled=auto_payment.lower() == 'true')
        
        # Filter by due date range
        due_from = self.request.query_params.get('due_from')
        due_to = self.request.query_params.get('due_to')
        if due_from:
            queryset = queryset.filter(due_date__gte=due_from)
        if due_to:
            queryset = queryset.filter(due_date__lte=due_to)
        
        # Filter by amount range
        min_amount = self.request.query_params.get('min_amount')
        max_amount = self.request.query_params.get('max_amount')
        if min_amount:
            queryset = queryset.filter(amount_due__gte=min_amount)
        if max_amount:
            queryset = queryset.filter(amount_due__lte=max_amount)
        
        # Filter by installment
        installment_number = self.request.query_params.get('installment_number')
        if installment_number:
            queryset = queryset.filter(installment_number=installment_number)
        
        # Filter overdue schedules
        overdue_only = self.request.query_params.get('overdue_only')
        if overdue_only and overdue_only.lower() == 'true':
            today = timezone.now().date()
            queryset = queryset.filter(
                due_date__lt=today,
                status__in=['pending', 'scheduled', 'failed']
            )
        
        # Filter due today
        due_today = self.request.query_params.get('due_today')
        if due_today and due_today.lower() == 'true':
            today = timezone.now().date()
            queryset = queryset.filter(due_date=today)
        
        # Filter upcoming (due in next N days)
        upcoming_days = self.request.query_params.get('upcoming_days')
        if upcoming_days:
            try:
                days = int(upcoming_days)
                today = timezone.now().date()
                future_date = today + timedelta(days=days)
                queryset = queryset.filter(
                    due_date__gte=today,
                    due_date__lte=future_date,
                    status__in=['pending', 'scheduled']
                )
            except ValueError:
                pass
        
        # Filter completed schedules
        completed_only = self.request.query_params.get('completed_only')
        if completed_only and completed_only.lower() == 'true':
            queryset = queryset.filter(status='completed')
        
        # Filter failed schedules
        failed_only = self.request.query_params.get('failed_only')
        if failed_only and failed_only.lower() == 'true':
            queryset = queryset.filter(status='failed')
        
        # Filter pending schedules
        pending_only = self.request.query_params.get('pending_only')
        if pending_only and pending_only.lower() == 'true':
            queryset = queryset.filter(status__in=['pending', 'scheduled'])
        
        # Filter by payment gateway
        payment_gateway = self.request.query_params.get('payment_gateway')
        if payment_gateway:
            queryset = queryset.filter(payment_gateway=payment_gateway)
        
        # Search by transaction reference, customer details, or case number
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(transaction_reference__icontains=search) |
                Q(renewal_case__customer__first_name__icontains=search) |
                Q(renewal_case__customer__last_name__icontains=search) |
                Q(renewal_case__customer__customer_code__icontains=search) |
                Q(renewal_case__case_number__icontains=search) |
                Q(renewal_case__policy__policy_number__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset.select_related(
            'renewal_case',
            'renewal_case__customer',
            'renewal_case__policy'
        ).order_by('due_date', 'installment_number')
    
    def perform_create(self, serializer):
        """Create payment schedule"""
        serializer.save(created_by=self.request.user)


class PaymentScheduleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete payment schedule.
    """
    queryset = PaymentSchedule.objects.filter(is_deleted=False)
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return PaymentScheduleUpdateSerializer
        return PaymentScheduleSerializer
    
    def perform_update(self, serializer):
        """Update payment schedule"""
        serializer.save(updated_by=self.request.user)
    
    def perform_destroy(self, instance):
        """Soft delete the payment schedule"""
        instance.delete(user=self.request.user)


@api_view(['GET'])
def payment_schedules_by_renewal_case(request, renewal_case_id):
    """
    Get all payment schedules for a specific renewal case.
    """
    schedules = PaymentSchedule.objects.filter(
        renewal_case_id=renewal_case_id,
        is_deleted=False
    ).order_by('installment_number')
    
    serializer = PaymentScheduleListSerializer(schedules, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def payment_schedules_by_customer(request, customer_id):
    """
    Get all payment schedules for a specific customer.
    """
    schedules = PaymentSchedule.objects.filter(
        renewal_case__customer_id=customer_id,
        is_deleted=False
    ).order_by('due_date', 'installment_number')
    
    serializer = PaymentScheduleListSerializer(schedules, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def process_scheduled_payment(request, schedule_id):
    """
    Process a scheduled payment.
    """
    schedule = get_object_or_404(PaymentSchedule, id=schedule_id, is_deleted=False)
    
    serializer = PaymentProcessingSerializer(
        data=request.data,
        context={'schedule': schedule}
    )
    
    if serializer.is_valid():
        processed_amount = serializer.validated_data['processed_amount']
        transaction_reference = serializer.validated_data.get('transaction_reference', '')
        
        try:
            if processed_amount >= schedule.amount_due:
                schedule.mark_as_completed(processed_amount, transaction_reference)
                message = 'Payment completed successfully'
            else:
                schedule.process_partial_payment(processed_amount, transaction_reference)
                message = 'Partial payment processed successfully'
            
            return Response({
                'message': message,
                'schedule_id': schedule.id,
                'processed_amount': processed_amount,
                'remaining_amount': schedule.remaining_amount,
                'new_status': schedule.status
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def reschedule_payment(request, schedule_id):
    """
    Reschedule a payment to new due date.
    """
    schedule = get_object_or_404(PaymentSchedule, id=schedule_id, is_deleted=False)
    
    serializer = PaymentRescheduleSerializer(data=request.data)
    
    if serializer.is_valid():
        new_due_date = serializer.validated_data['new_due_date']
        reschedule_reason = serializer.validated_data.get('reschedule_reason', '')
        
        old_due_date = schedule.due_date
        schedule.reschedule_payment(new_due_date, reschedule_reason)
        
        return Response({
            'message': 'Payment rescheduled successfully',
            'schedule_id': schedule.id,
            'old_due_date': old_due_date,
            'new_due_date': new_due_date,
            'reschedule_count': schedule.reschedule_count
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def mark_payment_failed(request, schedule_id):
    """
    Mark a scheduled payment as failed.
    """
    schedule = get_object_or_404(PaymentSchedule, id=schedule_id, is_deleted=False)
    
    serializer = PaymentFailureSerializer(data=request.data)
    
    if serializer.is_valid():
        failure_reason = serializer.validated_data.get('failure_reason', '')
        failure_code = serializer.validated_data.get('failure_code', '')
        
        schedule.mark_as_failed(failure_reason, failure_code)
        
        return Response({
            'message': 'Payment marked as failed',
            'schedule_id': schedule.id,
            'retry_count': schedule.retry_count,
            'can_retry': schedule.can_retry,
            'next_retry_date': schedule.next_retry_date
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def setup_auto_payment(request, schedule_id):
    """
    Setup or update auto payment for a schedule.
    """
    schedule = get_object_or_404(PaymentSchedule, id=schedule_id, is_deleted=False)
    
    serializer = AutoPaymentSerializer(data=request.data)
    
    if serializer.is_valid():
        auto_payment_enabled = serializer.validated_data['auto_payment_enabled']
        
        if auto_payment_enabled:
            auto_payment_method = serializer.validated_data.get('auto_payment_method', '')
            payment_gateway = serializer.validated_data.get('payment_gateway', '')
            gateway_schedule_id = serializer.validated_data.get('gateway_schedule_id', '')
            
            schedule.enable_auto_payment(
                auto_payment_method,
                payment_gateway,
                gateway_schedule_id
            )
            message = 'Auto payment enabled successfully'
        else:
            schedule.disable_auto_payment()
            message = 'Auto payment disabled successfully'
        
        return Response({
            'message': message,
            'schedule_id': schedule.id,
            'auto_payment_enabled': schedule.auto_payment_enabled,
            'auto_payment_method': schedule.auto_payment_method
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def send_payment_reminder(request, schedule_id):
    """
    Send payment reminder for a schedule.
    """
    schedule = get_object_or_404(PaymentSchedule, id=schedule_id, is_deleted=False)
    
    schedule.send_reminder()
    
    return Response({
        'message': 'Payment reminder sent successfully',
        'schedule_id': schedule.id,
        'reminder_count': schedule.reminder_count,
        'reminder_date': schedule.reminder_date
    })


@api_view(['POST'])
def notify_customer(request, schedule_id):
    """
    Mark customer as notified about payment schedule.
    """
    schedule = get_object_or_404(PaymentSchedule, id=schedule_id, is_deleted=False)
    
    schedule.notify_customer()
    
    return Response({
        'message': 'Customer notified successfully',
        'schedule_id': schedule.id,
        'notification_date': schedule.notification_date
    })


@api_view(['POST'])
def create_bulk_schedules(request):
    """
    Create multiple payment schedules for installment payments.
    """
    serializer = BulkScheduleCreateSerializer(data=request.data)
    
    if serializer.is_valid():
        data = serializer.validated_data
        
        renewal_case_id = data['renewal_case']
        total_amount = data['total_amount']
        installment_count = data['installment_count']
        first_due_date = data['first_due_date']
        payment_method = data['payment_method']
        payment_frequency = data['payment_frequency']
        grace_period_days = data['grace_period_days']
        auto_payment_enabled = data['auto_payment_enabled']
        description = data.get('description', '')
        
        # Calculate installment amount
        installment_amount = (total_amount / installment_count).quantize(Decimal('0.01'))
        
        # Calculate frequency delta
        frequency_map = {
            'monthly': 30,
            'quarterly': 90,
            'half_yearly': 180,
            'yearly': 365,
            'custom': 30,  # Default to monthly for custom
        }
        
        frequency_days = frequency_map.get(payment_frequency, 30)
        
        schedules = []
        current_due_date = first_due_date
        
        for i in range(installment_count):
            # Adjust last installment for rounding differences
            if i == installment_count - 1:
                remaining_amount = total_amount - (installment_amount * (installment_count - 1))
                current_amount = remaining_amount
            else:
                current_amount = installment_amount
            
            schedule = PaymentSchedule.objects.create(
                renewal_case_id=renewal_case_id,
                due_date=current_due_date,
                amount_due=current_amount,
                payment_method=payment_method,
                installment_number=i + 1,
                total_installments=installment_count,
                description=f"{description} - Installment {i + 1}/{installment_count}",
                grace_period_days=grace_period_days,
                auto_payment_enabled=auto_payment_enabled,
                created_by=request.user
            )
            
            schedules.append(schedule)
            
            # Calculate next due date
            if i < installment_count - 1:
                current_due_date += timedelta(days=frequency_days)
        
        serializer_response = PaymentScheduleListSerializer(schedules, many=True)
        
        return Response({
            'message': f'{installment_count} payment schedules created successfully',
            'total_amount': total_amount,
            'installment_amount': installment_amount,
            'schedules': serializer_response.data
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def payment_schedule_statistics(request):
    """
    Get statistics about payment schedules.
    """
    schedules = PaymentSchedule.objects.filter(is_deleted=False)
    
    # Status distribution
    status_distribution = {}
    for choice in PaymentSchedule.PAYMENT_STATUS_CHOICES:
        status_key = choice[0]
        count = schedules.filter(status=status_key).count()
        status_distribution[status_key] = count
    
    # Payment method distribution
    method_distribution = {}
    for choice in PaymentSchedule.PAYMENT_METHOD_CHOICES:
        method_key = choice[0]
        count = schedules.filter(payment_method=method_key).count()
        method_distribution[method_key] = count
    
    # Due date analysis
    today = timezone.now().date()
    overdue_count = schedules.filter(
        due_date__lt=today,
        status__in=['pending', 'scheduled', 'failed']
    ).count()
    
    due_today_count = schedules.filter(
        due_date=today,
        status__in=['pending', 'scheduled']
    ).count()
    
    upcoming_7_days = schedules.filter(
        due_date__gte=today,
        due_date__lte=today + timedelta(days=7),
        status__in=['pending', 'scheduled']
    ).count()
    
    upcoming_30_days = schedules.filter(
        due_date__gte=today,
        due_date__lte=today + timedelta(days=30),
        status__in=['pending', 'scheduled']
    ).count()
    
    # Auto payment analysis
    auto_payment_enabled = schedules.filter(auto_payment_enabled=True).count()
    auto_payment_disabled = schedules.filter(auto_payment_enabled=False).count()
    
    # Amount analysis
    amount_ranges = {
        'under_1000': schedules.filter(amount_due__lt=1000).count(),
        '1000_to_5000': schedules.filter(amount_due__gte=1000, amount_due__lt=5000).count(),
        '5000_to_10000': schedules.filter(amount_due__gte=5000, amount_due__lt=10000).count(),
        '10000_to_50000': schedules.filter(amount_due__gte=10000, amount_due__lt=50000).count(),
        '50000_to_100000': schedules.filter(amount_due__gte=50000, amount_due__lt=100000).count(),
        'above_100000': schedules.filter(amount_due__gte=100000).count(),
    }
    
    # Aggregate statistics
    aggregates = schedules.aggregate(
        total_schedules=Count('id'),
        total_amount_due=Sum('amount_due'),
        total_processed_amount=Sum('processed_amount'),
        avg_amount_due=Avg('amount_due'),
        max_amount_due=Max('amount_due'),
        min_amount_due=Min('amount_due'),
        avg_installments=Avg('total_installments'),
        max_installments=Max('total_installments')
    )
    
    return Response({
        'total_schedules': aggregates['total_schedules'],
        'total_amount_due': aggregates['total_amount_due'],
        'total_processed_amount': aggregates['total_processed_amount'],
        'pending_amount': (aggregates['total_amount_due'] or 0) - (aggregates['total_processed_amount'] or 0),
        'average_amount_due': aggregates['avg_amount_due'],
        'max_amount_due': aggregates['max_amount_due'],
        'min_amount_due': aggregates['min_amount_due'],
        'average_installments': aggregates['avg_installments'],
        'max_installments': aggregates['max_installments'],
        'overdue_count': overdue_count,
        'due_today_count': due_today_count,
        'upcoming_7_days_count': upcoming_7_days,
        'upcoming_30_days_count': upcoming_30_days,
        'auto_payment_enabled_count': auto_payment_enabled,
        'auto_payment_disabled_count': auto_payment_disabled,
        'status_distribution': status_distribution,
        'payment_method_distribution': method_distribution,
        'amount_distribution': amount_ranges,
    })


@api_view(['GET'])
def payment_schedule_summary(request):
    """
    Get summary of all payment schedules for analytics.
    """
    schedules = PaymentSchedule.objects.filter(is_deleted=False)
    serializer = PaymentScheduleSummarySerializer(schedules, many=True)
    return Response(serializer.data)
