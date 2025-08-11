from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Sum
from .models import PolicyAdditionalBenefit
from .serializers import PolicyAdditionalBenefitSerializer, PolicyAdditionalBenefitListSerializer
from apps.core.pagination import StandardResultsSetPagination


class PolicyAdditionalBenefitViewSet(viewsets.ModelViewSet):
    """ViewSet for managing policy additional benefits"""
    
    queryset = PolicyAdditionalBenefit.objects.select_related(
        'policy', 'policy__customer', 'policy__policy_type'
    ).filter(is_deleted=False)
    
    serializer_class = PolicyAdditionalBenefitSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = [
        'policy', 'benefit_type', 'is_active', 'is_optional'
    ]
    
    search_fields = [
        'benefit_name', 'benefit_description', 'policy__policy_number',
        'policy__customer__name', 'policy__customer__email'
    ]
    
    ordering_fields = [
        'created_at', 'updated_at', 'benefit_name', 'display_order', 
        'coverage_amount', 'premium_impact'
    ]
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return PolicyAdditionalBenefitListSerializer
        return PolicyAdditionalBenefitSerializer
    
    def perform_create(self, serializer):
        """Set created_by when creating a new policy additional benefit"""
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        """Set updated_by when updating a policy additional benefit"""
        serializer.save(updated_by=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Create a new policy additional benefit"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response({
            'success': True,
            'message': 'Policy additional benefit created successfully',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def list(self, request, *args, **kwargs):
        """List all policy additional benefits with filtering and pagination"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'success': True,
                'message': 'Policy additional benefits retrieved successfully',
                'data': serializer.data
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'message': 'Policy additional benefits retrieved successfully',
            'data': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def by_policy(self, request):
        """Get all additional benefits for a specific policy"""
        policy_id = request.query_params.get('policy_id')
        
        if not policy_id:
            return Response({
                'success': False,
                'message': 'Policy ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        benefits = self.get_queryset().filter(policy_id=policy_id)
        serializer = PolicyAdditionalBenefitListSerializer(benefits, many=True)
        
        total_premium_impact = benefits.aggregate(
            total=Sum('premium_impact')
        )['total'] or 0
        
        return Response({
            'success': True,
            'message': 'Policy additional benefits retrieved successfully',
            'data': serializer.data,
            'total_premium_impact': total_premium_impact
        })
    
    @action(detail=False, methods=['get'])
    def benefit_types(self, request):
        """Get all available benefit types"""
        benefit_types = [
            {'value': choice[0], 'label': choice[1]} 
            for choice in PolicyAdditionalBenefit.BENEFIT_TYPE_CHOICES
        ]
        
        return Response({
            'success': True,
            'message': 'Benefit types retrieved successfully',
            'data': benefit_types
        })
