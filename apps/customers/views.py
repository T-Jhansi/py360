# views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from .models import Customer
from .serializers import CustomerSerializer

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    @action(detail=False, methods=['post'])
    def update_policy_counts(self, request):
        """Update policy counts for all customers"""
        try:
            customers = Customer.objects.all()
            updated_count = 0

            with transaction.atomic():
                for customer in customers:
                    customer.update_metrics()
                    updated_count += 1

            return Response({
                'message': f'Successfully updated policy counts for {updated_count} customers',
                'updated_count': updated_count
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': f'Failed to update policy counts: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def update_policy_count(self, request, pk=None):
        """Update policy count for a specific customer"""
        try:
            customer = self.get_object()
            old_count = customer.total_policies
            customer.update_metrics()
            new_count = customer.total_policies

            return Response({
                'message': f'Updated policy count for customer {customer.customer_code}',
                'customer_code': customer.customer_code,
                'old_count': old_count,
                'new_count': new_count
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': f'Failed to update policy count: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
