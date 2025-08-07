from rest_framework import viewsets, status
from rest_framework.response import Response
from django.db.models import Q
from apps.core.pagination import StandardResultsSetPagination
from .models import CustomerFinancialProfile
from .serializers import (
    CustomerFinancialProfileSerializer,
    CustomerFinancialProfileCreateSerializer,
    CustomerFinancialProfileListSerializer
)

class CustomerFinancialProfileViewSet(viewsets.ModelViewSet):
    queryset = CustomerFinancialProfile.objects.filter(is_deleted=False)
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomerFinancialProfileCreateSerializer
        return CustomerFinancialProfileListSerializer

    def get_queryset(self):
        queryset = CustomerFinancialProfile.objects.filter(is_deleted=False)

        # Filter by customer
        customer_id = self.request.query_params.get('customer_id')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)

        # Filter by risk profile
        risk_profile = self.request.query_params.get('risk_profile')
        if risk_profile:
            queryset = queryset.filter(risk_profile=risk_profile)

        # Filter by income range
        min_income = self.request.query_params.get('min_income')
        max_income = self.request.query_params.get('max_income')
        if min_income:
            queryset = queryset.filter(annual_income__gte=min_income)
        if max_income:
            queryset = queryset.filter(annual_income__lte=max_income)

        # Search by customer name or code
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(customer__first_name__icontains=search) |
                Q(customer__last_name__icontains=search) |
                Q(customer__company_name__icontains=search) |
                Q(customer__customer_code__icontains=search)
            )

        return queryset.select_related('customer').order_by('-created_at')

    def list(self, request, *args, **kwargs):
        """List customer financial profiles with success response"""
        try:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)

            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response({
                    'success': True,
                    'message': 'Customer financial profiles retrieved successfully',
                    'data': serializer.data
                })

            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'success': True,
                'message': 'Customer financial profiles retrieved successfully',
                'count': queryset.count(),
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error retrieving customer financial profiles: {str(e)}',
                'data': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request, *args, **kwargs):
        """Create/Store new customer financial profile"""
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                # Save the financial profile and update capacity utilization
                financial_profile = serializer.save(created_by=request.user)
                financial_profile.update_capacity_utilization()

                # Return success response with created data
                response_serializer = CustomerFinancialProfileSerializer(financial_profile)
                return Response({
                    'success': True,
                    'message': 'Customer financial profile created successfully',
                    'data': response_serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'message': 'Validation failed',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error creating customer financial profile: {str(e)}',
                'errors': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Disable other actions to keep only create and list
    def retrieve(self, request, *args, **kwargs):
        return Response({
            'success': False,
            'message': 'Retrieve action not available'
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs):
        return Response({
            'success': False,
            'message': 'Update action not available'
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, *args, **kwargs):
        return Response({
            'success': False,
            'message': 'Partial update action not available'
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, *args, **kwargs):
        return Response({
            'success': False,
            'message': 'Delete action not available'
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)



