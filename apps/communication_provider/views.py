from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta

from .models import CommunicationProvider
from .serializers import (
    CommunicationProviderSerializer,
    CommunicationProviderListSerializer,
    CommunicationProviderCreateSerializer
)


class CommunicationProviderViewSet(viewsets.ModelViewSet):    
    queryset = CommunicationProvider.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return CommunicationProviderListSerializer
        elif self.action == 'create':
            return CommunicationProviderCreateSerializer
        return CommunicationProviderSerializer

    def create(self, request, *args, **kwargs):
        """Override create to add success message"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        
        return Response({
            'success': True,
            'message': 'Communication provider created successfully!',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        """Override update to add success message"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'success': True,
            'message': 'Communication provider updated successfully!',
            'data': serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        """Override destroy to add success message"""
        instance = self.get_object()
        self.perform_destroy(instance)
        
        return Response({
            'success': True,
            'message': 'Communication provider deleted successfully!'
        }, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        """Override list to add success message"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            paginated_response.data.update({
                'success': True,
                'message': f'Retrieved {len(serializer.data)} communication provider(s) successfully!'
            })
            return paginated_response
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'message': f'Retrieved {len(serializer.data)} communication provider(s) successfully!',
            'data': serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to add success message"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return Response({
            'success': True,
            'message': 'Communication provider retrieved successfully!',
            'data': serializer.data
        })

    def get_queryset(self):
        queryset = super().get_queryset()

        query_params = getattr(self.request, 'query_params', self.request.GET)

        channel = query_params.get('channel', None)
        if channel:
            queryset = queryset.filter(channel=channel)

        is_active = query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        is_default = query_params.get('is_default', None)
        if is_default is not None:
            queryset = queryset.filter(is_default=is_default.lower() == 'true')

        search = query_params.get('search', None)
        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset.order_by('channel', 'name')

    @action(detail=False, methods=['get'])
    def by_channel(self, request):
        providers = self.get_queryset()
        grouped = {}
        
        for provider in providers:
            channel = provider.channel
            if channel not in grouped:
                grouped[channel] = []
            grouped[channel].append(CommunicationProviderListSerializer(provider).data)
        
        return Response({
            'success': True,
            'data': grouped
        })

    @action(detail=False, methods=['get'])
    def defaults(self, request):
        default_providers = self.get_queryset().filter(is_default=True)
        serializer = CommunicationProviderListSerializer(default_providers, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        })

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        provider = self.get_object()
        
        CommunicationProvider.objects.filter(
            channel=provider.channel,
            is_default=True,
            is_deleted=False
        ).exclude(pk=provider.pk).update(is_default=False, updated_by=request.user)
        
        provider.is_default = True
        provider.updated_by = request.user
        provider.save()
        
        return Response({
            'success': True,
            'message': f'{provider.name} is now the default {provider.channel} provider'
        })

    @action(detail=True, methods=['post'])
    def soft_delete(self, request, pk=None):
        provider = self.get_object()
        provider.soft_delete(user=request.user)
        
        return Response({
            'success': True,
            'message': f'{provider.name} has been soft deleted'
        })

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        provider = self.get_object()
        if not provider.is_deleted:
            return Response({
                'success': False,
                'message': 'Provider is not deleted'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        provider.restore(user=request.user)
        
        return Response({
            'success': True,
            'message': f'{provider.name} has been restored'
        })

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        queryset = self.get_queryset()
        
        total_providers = queryset.count()
        active_providers = queryset.filter(is_active=True).count()
        inactive_providers = queryset.filter(is_active=False).count()
        default_providers = queryset.filter(is_default=True).count()
        
        channel_stats = {}
        for channel, _ in CommunicationProvider.CHANNEL_CHOICES:
            channel_providers = queryset.filter(channel=channel)
            channel_stats[channel] = {
                'total': channel_providers.count(),
                'active': channel_providers.filter(is_active=True).count(),
                'default': channel_providers.filter(is_default=True).count()
            }
        
        return Response({
            'success': True,
            'data': {
                'total_providers': total_providers,
                'active_providers': active_providers,
                'inactive_providers': inactive_providers,
                'default_providers': default_providers,
                'by_channel': channel_stats
            }
        })

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
