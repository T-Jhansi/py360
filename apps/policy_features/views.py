from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.http import Http404
from .models import PolicyFeature
from .serializers import PolicyFeatureSerializer, PolicyFeatureListSerializer
from apps.core.pagination import StandardResultsSetPagination


class PolicyFeatureViewSet(viewsets.ModelViewSet):
    """ViewSet for managing policy features"""
    
    queryset = PolicyFeature.objects.select_related(
        'policy_type'
    ).filter(is_deleted=False)
    
    serializer_class = PolicyFeatureSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    # Filter fields
    filterset_fields = [
        'policy_type', 'feature_type', 'is_active', 'is_mandatory'
    ]

    # Search fields
    search_fields = [
        'feature_name', 'feature_description', 'policy_type__name',
        'policy_type__code', 'policy_type__category'
    ]
    
    # Ordering fields
    ordering_fields = [
        'created_at', 'updated_at', 'feature_name', 'display_order'
    ]
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return PolicyFeatureListSerializer
        return PolicyFeatureSerializer
    
    def perform_create(self, serializer):
        """Set created_by when creating a new policy feature"""
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        """Set updated_by when updating a policy feature"""
        serializer.save(updated_by=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Create a new policy feature"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response({
            'success': True,
            'message': 'Policy feature created successfully',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def list(self, request, *args, **kwargs):
        """List all policy features with filtering and pagination"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'success': True,
                'message': 'Policy features retrieved successfully',
                'data': serializer.data
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'message': 'Policy features retrieved successfully',
            'data': serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific policy feature by ID"""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response({
                'success': True,
                'message': 'Policy feature retrieved successfully',
                'data': serializer.data
            })
        except Http404:
            return Response({
                'success': False,
                'message': 'Policy features not available',
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def by_policy_type(self, request):
        """Get all features for a specific policy type"""
        policy_type_id = request.query_params.get('policy_type_id')

        if not policy_type_id:
            return Response({
                'success': False,
                'message': 'Policy type ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        features = self.get_queryset().filter(policy_type_id=policy_type_id)

        if not features.exists():
            return Response({
                'success': False,
                'message': 'Policy features not available',
                'data': []
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = PolicyFeatureListSerializer(features, many=True)

        return Response({
            'success': True,
            'message': 'Policy features retrieved successfully',
            'data': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def feature_types(self, request):
        """Get all available feature types"""
        feature_types = [
            {'value': choice[0], 'label': choice[1]} 
            for choice in PolicyFeature.FEATURE_TYPE_CHOICES
        ]
        
        return Response({
            'success': True,
            'message': 'Feature types retrieved successfully',
            'data': feature_types
        })
