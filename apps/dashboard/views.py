from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, Count, Q
from decimal import Decimal

from apps.renewals.models import RenewalCase
from apps.customer_payments.models import CustomerPayment
from .serializers import DashboardSummarySerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_summary(request):
    """
    Get dashboard summary data including renewal cases and payment statistics.
    
    Returns:
        JSON response with aggregated data from renewal_cases and customer_payments tables
    """
    try:
        # Get renewal cases data
        renewal_cases = RenewalCase.objects.filter(is_deleted=False)
        
        # Calculate renewal cases statistics
        total_cases = renewal_cases.count()
        in_progress = renewal_cases.filter(status='in_progress').count()
        renewed = renewal_cases.filter(status='renewed').count()
        pending_action = renewal_cases.filter(status='pending_action').count()
        failed = renewal_cases.filter(status='failed').count()
        
        # Calculate total renewal amount
        renewal_amount_total = renewal_cases.aggregate(
            total=Sum('renewal_amount')
        )['total'] or Decimal('0.00')
        
        # Get customer payments data
        payment_collected = CustomerPayment.objects.filter(
            is_deleted=False,
            payment_status='completed'
        ).aggregate(
            total=Sum('payment_amount')
        )['total'] or Decimal('0.00')
        
        # Calculate pending payment amount
        payment_pending = renewal_amount_total - payment_collected
        
        # Prepare response data
        dashboard_data = {
            'total_cases': total_cases,
            'in_progress': in_progress,
            'renewed': renewed,
            'pending_action': pending_action,
            'failed': failed,
            'renewal_amount_total': renewal_amount_total,
            'payment_collected': payment_collected,
            'payment_pending': payment_pending
        }
        
        # Serialize and return response
        serializer = DashboardSummarySerializer(dashboard_data)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch dashboard data: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
