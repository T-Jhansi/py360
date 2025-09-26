"""
Views for Outstanding Amounts functionality
"""

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from apps.renewals.models import RenewalCase
from apps.outstanding_amounts.services import OutstandingAmountsService
from apps.outstanding_amounts.serializers import (
    OutstandingAmountsSummarySerializer,
    PaymentInitiationSerializer,
    PaymentPlanSetupSerializer,
    PaymentResponseSerializer,
    PaymentPlanResponseSerializer
)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_outstanding_summary_api(request, case_id):
    try:
        # Handle both integer ID and case_number
        if case_id.isdigit():
            renewal_case = get_object_or_404(RenewalCase, id=int(case_id))
            actual_case_id = int(case_id)
        else:
            renewal_case = get_object_or_404(RenewalCase, case_number=case_id)
            actual_case_id = renewal_case.id
        
        # Get outstanding summary
        outstanding_data = OutstandingAmountsService.get_outstanding_summary(actual_case_id)
        
        if outstanding_data is None:
            return Response({
                'success': False,
                'error': 'Failed to calculate outstanding amounts'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Serialize the data
        serializer = OutstandingAmountsSummarySerializer(outstanding_data)
        
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': 'Failed to fetch outstanding amounts',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def initiate_payment_api(request, case_id):
    try:
        # Handle both integer ID and case_number
        if case_id.isdigit():
            renewal_case = get_object_or_404(RenewalCase, id=int(case_id))
            actual_case_id = int(case_id)
        else:
            renewal_case = get_object_or_404(RenewalCase, case_number=case_id)
            actual_case_id = renewal_case.id
        
        # Validate request data
        serializer = PaymentInitiationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'Invalid request data',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        
        # Prepare payment data
        payment_data = {
            'payment_mode': validated_data.get('payment_mode', 'upi'),
            'payment_notes': validated_data.get('payment_notes', '')
        }
        
        # Initiate payment
        result = OutstandingAmountsService.initiate_payment_for_case(
            case_id=actual_case_id,
            installment_ids=validated_data.get('installment_ids'),
            payment_data=payment_data
        )
        
        # Serialize response
        response_serializer = PaymentResponseSerializer(result)
        
        if result['success']:
            return Response({
                'success': True,
                'data': response_serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': result['message']
            }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': 'Failed to initiate payment',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def setup_payment_plan_api(request, case_id):
    try:
        # Handle both integer ID and case_number
        if case_id.isdigit():
            renewal_case = get_object_or_404(RenewalCase, id=int(case_id))
            actual_case_id = int(case_id)
        else:
            renewal_case = get_object_or_404(RenewalCase, case_number=case_id)
            actual_case_id = renewal_case.id
        
        # Validate request data
        serializer = PaymentPlanSetupSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'Invalid request data',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        
        # Setup payment plan
        result = OutstandingAmountsService.setup_payment_plan_for_case(
            case_id=actual_case_id,
            plan_data=validated_data
        )
        
        # Serialize response
        response_serializer = PaymentPlanResponseSerializer(result)
        
        if result['success']:
            return Response({
                'success': True,
                'data': response_serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': result['message']
            }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': 'Failed to setup payment plan',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
