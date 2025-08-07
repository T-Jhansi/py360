from rest_framework import status, viewsets
from rest_framework.response import Response
from django.db.models import Q
from .models import CustomerAssets
from .serializers import (
    CustomerAssetsSerializer,
    CustomerAssetsCreateSerializer,
    CustomerAssetsUpdateSerializer,
    CustomerAssetsListSerializer
)


class CustomerAssetsViewSet(viewsets.ModelViewSet):
    queryset = CustomerAssets.objects.filter(is_deleted=False)

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomerAssetsCreateSerializer
        elif self.action == 'list':
            return CustomerAssetsListSerializer
        elif self.action in ['update', 'partial_update']:
            return CustomerAssetsUpdateSerializer
        return CustomerAssetsSerializer

    def get_queryset(self):
        queryset = CustomerAssets.objects.filter(is_deleted=False)

        customer_id = self.request.query_params.get('customer_id')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)

        residence_type = self.request.query_params.get('residence_type')
        if residence_type:
            queryset = queryset.filter(residence_type=residence_type)

        residence_status = self.request.query_params.get('residence_status')
        if residence_status:
            queryset = queryset.filter(residence_status=residence_status)

        residence_rating = self.request.query_params.get('residence_rating')
        if residence_rating:
            queryset = queryset.filter(residence_rating=residence_rating)

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(customer__first_name__icontains=search) |
                Q(customer__last_name__icontains=search) |
                Q(customer__company_name__icontains=search) |
                Q(customer__customer_code__icontains=search) |
                Q(residence_location__icontains=search)
            )

        return queryset.select_related('customer').order_by('-created_at')

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                customer_assets = serializer.save(created_by=request.user)

                response_serializer = CustomerAssetsSerializer(customer_assets)
                return Response({
                    'success': True,
                    'message': 'Customer assets stored successfully',
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
                'message': f'Error storing customer assets: {str(e)}',
                'errors': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)

            return Response({
                'success': True,
                'message': 'Customer assets retrieved successfully',
                'count': queryset.count(),
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error retrieving customer assets: {str(e)}',
                'data': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        instance.delete(user=self.request.user)
