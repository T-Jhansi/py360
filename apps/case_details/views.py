from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from apps.customers.models import Customer
from apps.renewals.models import RenewalCase
from .serializers import CustomerSerializer
from apps.customers.models import Customer
from apps.customer_communication_preferences.models import CustomerCommunicationPreference
from .serializers import CustomerCommunicationPreferenceSerializer

# OverView & Policy

class CombinedPolicyDataAPIView(APIView):
    """
    API View to fetch combined policy data from multiple tables using nested serializers
    """

    def get(self, request, case_id=None):

        try:
            if case_id is None:
                case_id = request.query_params.get('case_id')
                if not case_id:
                    return Response({
                        'success': False,
                        'message': 'case_id parameter is required',
                        'data': None
                    }, status=status.HTTP_400_BAD_REQUEST)

            # Get the renewal case
            renewal_case = get_object_or_404(RenewalCase, id=case_id)

            # Get the customer with all related data using optimized queries
            customer = get_object_or_404(
                Customer.objects.select_related(
                    'financial_profile'
                ).prefetch_related(
                    'documents_new',
                    'channels',
                    'policies__policy_type',
                    'policies__policy_type__policy_features',
                    'policies__policy_type__policy_coverages',
                    'policies__policy_type__policy_coverages__additional_benefits',
                    'policies__exclusions'
                ),
                id=renewal_case.policy.customer.id
            )

            # Serialize the customer data with all nested relationships
            serializer = CustomerSerializer(customer)

            return Response({
                'success': True,
                'message': 'Combined policy data retrieved successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        except RenewalCase.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Renewal case not found',
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)

        except Customer.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Customer not found',
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error retrieving combined policy data: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

# Preferences

class CustomerCommunicationPreferencesAPIView(APIView):
    def get(self, request, case_number):
        try:
            renewal_case = RenewalCase.objects.get(case_number=case_number)
            preferences = CustomerCommunicationPreference.objects.filter(case=renewal_case)
            serializer = CustomerCommunicationPreferenceSerializer(preferences, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except RenewalCase.DoesNotExist:
            return Response({"error": "Case not found"}, status=status.HTTP_404_NOT_FOUND)
        
