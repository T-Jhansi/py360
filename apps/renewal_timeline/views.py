from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import RenewalTimeline
from typing import Any
from .serializers import (
    RenewalTimelineListSerializer,
    RenewalTimelineDetailSerializer,
    RenewalTimelineCreateSerializer,
)


class RenewalTimelineViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return RenewalTimeline.objects.select_related(  # type: ignore[attr-defined]
            'customer', 'policy', 'preferred_channel', 'renewal_case', 'last_payment'
        )
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['customer', 'policy', 'renewal_case', 'preferred_channel', 'is_active', 'auto_renewal_enabled']
    search_fields = ['notes', 'renewal_pattern']
    ordering_fields = ['next_due_date', 'created_at', 'updated_at']
    ordering = ['-updated_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return RenewalTimelineListSerializer
        if self.action == 'create':
            return RenewalTimelineCreateSerializer
        if self.action in ['retrieve', 'update', 'partial_update']:
            return RenewalTimelineDetailSerializer
        return RenewalTimelineDetailSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


