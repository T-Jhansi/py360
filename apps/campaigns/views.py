# views.py

from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Campaign
from .serializers import CampaignSerializer
from apps.core.pagination import StandardResultsSetPagination

class CampaignViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Campaigns"""
    queryset = Campaign.objects.select_related('campaign_type', 'created_by', 'assigned_to')
    serializer_class = CampaignSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'campaign_type', 'target_audience']
    search_fields = ['name', 'description']
    ordering_fields = ['started_date', 'created_at']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save()
