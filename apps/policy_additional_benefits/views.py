from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Sum
from .models import PolicyAdditionalBenefit
from .serializers import (
    PolicyAdditionalBenefitSerializer,
    PolicyAdditionalBenefitListSerializer,
    PolicyAdditionalBenefitStoreSerializer,
    PolicyAdditionalBenefitDetailSerializer
)
from apps.core.pagination import StandardResultsSetPagination


class PolicyAdditionalBenefitViewSet(viewsets.ModelViewSet):
    """ViewSet for managing policy additional benefits"""
    
    queryset = PolicyAdditionalBenefit.objects.select_related(
        'policy_coverages', 'policy_coverages__policy_type'
    ).filter(is_deleted=False)

    serializer_class = PolicyAdditionalBenefitSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    filterset_fields = [
        'policy_coverages', 'benefit_category', 'benefit_type', 'is_active', 'is_optional'
    ]

    search_fields = [
        'benefit_name', 'benefit_description', 'benefit_category',
        'policy_coverages__coverage_name', 'policy_coverages__policy_type__name'
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
    def by_policy_coverage(self, request):
        """Get all additional benefits for a specific policy coverage"""
        policy_coverage_id = request.query_params.get('policy_coverage_id')

        if not policy_coverage_id:
            return Response({
                'success': False,
                'message': 'Policy coverage ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        benefits = self.get_queryset().filter(policy_coverages_id=policy_coverage_id)
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
    def by_policy_type(self, request):
        """Get all additional benefits for a specific policy type"""
        policy_type_id = request.query_params.get('policy_type_id')

        if not policy_type_id:
            return Response({
                'success': False,
                'message': 'Policy type ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        benefits = self.get_queryset().filter(policy_coverages__policy_type_id=policy_type_id)
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

    @action(detail=False, methods=['post'])
    def store(self, request):
        """Store new policy additional benefit based on image structure"""
        serializer = PolicyAdditionalBenefitStoreSerializer(data=request.data)

        if serializer.is_valid():
            # Set created_by if user is authenticated
            benefit = serializer.save()
            if hasattr(request, 'user') and request.user.is_authenticated:
                benefit.created_by = request.user
                benefit.save()

            # Return detailed response
            response_serializer = PolicyAdditionalBenefitDetailSerializer(benefit)
            return Response({
                'success': True,
                'message': 'Policy additional benefit created successfully',
                'data': response_serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({
            'success': False,
            'message': 'Validation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def list_benefits(self, request):
        """List policy additional benefits based on image structure with filtering"""
        queryset = self.get_queryset()

        # Filter by policy_coverage_id if provided
        policy_coverage_id = request.query_params.get('policy_coverage_id')
        if policy_coverage_id:
            queryset = queryset.filter(policy_coverages_id=policy_coverage_id)

        # Filter by benefit_category if provided
        benefit_category = request.query_params.get('benefit_category')
        if benefit_category:
            queryset = queryset.filter(benefit_category__icontains=benefit_category)

        # Filter by is_active if provided
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            is_active_bool = is_active.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_active=is_active_bool)

        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = PolicyAdditionalBenefitDetailSerializer(page, many=True)
            return self.get_paginated_response({
                'success': True,
                'message': 'Policy additional benefits retrieved successfully',
                'data': serializer.data
            })

        serializer = PolicyAdditionalBenefitDetailSerializer(queryset, many=True)
        return Response({
            'success': True,
            'message': 'Policy additional benefits retrieved successfully',
            'data': serializer.data,
            'total_count': queryset.count()
        })

    @action(detail=False, methods=['get'])
    def grouped_by_category(self, request):
        """Get benefits grouped by category for frontend display like in the image"""
        policy_coverage_id = request.query_params.get('policy_coverage_id')

        if not policy_coverage_id:
            return Response({
                'success': False,
                'message': 'Policy coverage ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.get_queryset().filter(
            policy_coverages_id=policy_coverage_id,
            is_active=True
        ).order_by('benefit_category', 'display_order', 'benefit_name')

        # Group benefits by category
        grouped_benefits = {}
        for benefit in queryset:
            category = benefit.benefit_category or 'Other'
            if category not in grouped_benefits:
                grouped_benefits[category] = []

            benefit_data = PolicyAdditionalBenefitDetailSerializer(benefit).data
            grouped_benefits[category].append(benefit_data)

        return Response({
            'success': True,
            'message': 'Grouped benefits retrieved successfully',
            'data': grouped_benefits
        })
