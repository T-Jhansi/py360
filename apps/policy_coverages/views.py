from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Sum, Count
from .models import PolicyCoverage
from .serializers import (
    PolicyCoverageSerializer, 
    PolicyCoverageListSerializer,
    PolicyCoverageSummarySerializer
)
from apps.core.pagination import StandardResultsSetPagination


class PolicyCoverageViewSet(viewsets.ModelViewSet):
    """ViewSet for managing policy coverages"""
    
    queryset = PolicyCoverage.objects.select_related(
        'policy', 'policy__customer', 'policy__policy_type'
    ).filter(is_deleted=False)
    
    serializer_class = PolicyCoverageSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = [
        'policy', 'coverage_type', 'coverage_category', 'is_included', 'is_optional'
    ]
    
    search_fields = [
        'coverage_name', 'coverage_description', 'policy__policy_number',
        'policy__customer__name', 'policy__customer__email'
    ]
    
    ordering_fields = [
        'created_at', 'updated_at', 'coverage_name', 'display_order', 
        'coverage_amount', 'premium_impact'
    ]
    ordering = ['coverage_type', 'display_order', 'coverage_name']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return PolicyCoverageListSerializer
        elif self.action in ['coverage_summary', 'by_policy_summary']:
            return PolicyCoverageSummarySerializer
        return PolicyCoverageSerializer
    
    def perform_create(self, serializer):
        """Set created_by when creating a new policy coverage"""
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        """Set updated_by when updating a policy coverage"""
        serializer.save(updated_by=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Create a new policy coverage"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response({
            'success': True,
            'message': 'Policy coverage created successfully',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def list(self, request, *args, **kwargs):
        """List all policy coverages with filtering and pagination"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'success': True,
                'message': 'Policy coverages retrieved successfully',
                'data': serializer.data
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'message': 'Policy coverages retrieved successfully',
            'data': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def by_policy(self, request):
        """Get all coverages for a specific policy"""
        policy_id = request.query_params.get('policy_id')
        
        if not policy_id:
            return Response({
                'success': False,
                'message': 'Policy ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        coverages = self.get_queryset().filter(policy_id=policy_id)
        serializer = PolicyCoverageListSerializer(coverages, many=True)
        
        # Calculate totals
        totals = coverages.aggregate(
            total_coverage_amount=Sum('coverage_amount'),
            total_premium_impact=Sum('premium_impact'),
            total_coverages=Count('id')
        )
        
        return Response({
            'success': True,
            'message': 'Policy coverages retrieved successfully',
            'data': serializer.data,
            'totals': totals
        })
    
    @action(detail=False, methods=['get'])
    def by_policy_summary(self, request):
        """Get coverage summary for a specific policy"""
        policy_id = request.query_params.get('policy_id')
        
        if not policy_id:
            return Response({
                'success': False,
                'message': 'Policy ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        coverages = self.get_queryset().filter(policy_id=policy_id, is_included=True)
        serializer = self.get_serializer(coverages, many=True)
        
        return Response({
            'success': True,
            'message': 'Policy coverage summary retrieved successfully',
            'data': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def coverage_types(self, request):
        """Get all available coverage types"""
        coverage_types = [
            {'value': choice[0], 'label': choice[1]} 
            for choice in PolicyCoverage.COVERAGE_TYPE_CHOICES
        ]
        
        return Response({
            'success': True,
            'message': 'Coverage types retrieved successfully',
            'data': coverage_types
        })
    
    @action(detail=False, methods=['get'])
    def coverage_categories(self, request):
        """Get all available coverage categories"""
        coverage_categories = [
            {'value': choice[0], 'label': choice[1]} 
            for choice in PolicyCoverage.COVERAGE_CATEGORY_CHOICES
        ]
        
        return Response({
            'success': True,
            'message': 'Coverage categories retrieved successfully',
            'data': coverage_categories
        })
