from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404

from .models import CommonRenewalTimelineSettings
from typing import Any
from .serializers import (
    CommonRenewalTimelineSettingsSerializer,
    CommonRenewalTimelineSettingsCreateSerializer,
)


class CommonRenewalTimelineSettingsViewSet(viewsets.ModelViewSet):
    """ViewSet for managing common renewal timeline settings"""
    
    def get_queryset(self):
        return CommonRenewalTimelineSettings.objects.all()
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'auto_renewal_enabled']
    search_fields = ['renewal_pattern', 'description']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return CommonRenewalTimelineSettingsCreateSerializer
        return CommonRenewalTimelineSettingsSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                'success': True,
                'message': 'Common renewal timeline settings created successfully',
                'data': serializer.data,
            },
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    @action(detail=False, methods=['post'], url_path='save-common-timeline-settings')
    def save_common_timeline_settings(self, request):
        """
        Save common renewal timeline settings that apply to all customers
        Expected payload matches the frontend structure:
        {
            "renewal_pattern": "Pays 7-14 days before due date",
            "reminder_schedule": [
                {"days": 30, "channel": "Email"},
                {"days": 14, "channel": "Email"}, 
                {"days": 7, "channel": "Phone"}
            ],
            "auto_renewal_enabled": false,
            "description": "Default renewal timeline settings for all customers"
        }
        """
        try:
            # Extract data from request
            renewal_pattern = request.data.get('renewal_pattern', '')
            reminder_schedule = request.data.get('reminder_schedule', [])
            auto_renewal_enabled = request.data.get('auto_renewal_enabled', False)
            description = request.data.get('description', '')
            
            # Convert reminder schedule to reminder_days format
            reminder_days = []
            formatted_reminder_schedule = []
            for reminder in reminder_schedule:
                if isinstance(reminder, dict) and 'days' in reminder:
                    days = reminder['days']
                    channel = reminder.get('channel', 'Email')
                    reminder_days.append(days)
                    # Create formatted string for frontend display
                    formatted_reminder_schedule.append(f"{days} days before due date ({channel})")
            
            # Get or create common timeline settings (only one active setting)
            common_settings, created = CommonRenewalTimelineSettings.objects.get_or_create(
                is_active=True,
                defaults={
                    'renewal_pattern': renewal_pattern,
                    'reminder_days': reminder_days,
                    'reminder_schedule': formatted_reminder_schedule,
                    'auto_renewal_enabled': auto_renewal_enabled,
                    'description': description,
                    'created_by': request.user,
                    'updated_by': request.user,
                }
            )
            
            # Update existing settings if not created
            if not created:
                common_settings.renewal_pattern = renewal_pattern
                common_settings.reminder_days = reminder_days
                common_settings.reminder_schedule = formatted_reminder_schedule
                common_settings.auto_renewal_enabled = auto_renewal_enabled
                common_settings.description = description
                common_settings.updated_by = request.user
                common_settings.save()
            
            # Serialize the response
            serializer = CommonRenewalTimelineSettingsSerializer(common_settings)
            
            return Response({
                'success': True,
                'message': 'Common renewal timeline settings saved successfully',
                'data': serializer.data,
                'created': created
            }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error saving common timeline settings: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='get-common-timeline-settings')
    def get_common_timeline_settings(self, request):
        """
        Get common renewal timeline settings that apply to all customers
        No query params needed - returns the active common settings
        """
        try:
            # Get the active common timeline settings
            common_settings = CommonRenewalTimelineSettings.objects.filter(is_active=True).first()
            
            if not common_settings:
                return Response({
                    'success': False,
                    'message': 'No common timeline settings found. Please create settings first.',
                    'data': None
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Use the formatted reminder schedule if available, otherwise format from reminder_days
            if common_settings.reminder_schedule:
                formatted_reminder_schedule = common_settings.reminder_schedule
            else:
                # Fallback: format from reminder_days for backward compatibility
                formatted_reminder_schedule = []
                for days in common_settings.reminder_days:
                    if days == 30:
                        formatted_reminder_schedule.append("30 days before due date (Email)")
                    elif days == 14:
                        formatted_reminder_schedule.append("14 days before due date (Email)")
                    elif days == 7:
                        formatted_reminder_schedule.append("7 days before due date (Phone)")
                    else:
                        formatted_reminder_schedule.append(f"{days} days before due date (Email)")
            
            frontend_data = {
                'renewal_pattern': common_settings.renewal_pattern,
                'reminder_schedule': formatted_reminder_schedule,
                'auto_renewal_enabled': common_settings.auto_renewal_enabled,
                'description': common_settings.description,
                'is_active': common_settings.is_active,
                'created_at': common_settings.created_at,
                'updated_at': common_settings.updated_at
            }
            
            return Response({
                'success': True,
                'message': 'Common timeline settings retrieved successfully',
                'data': frontend_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error retrieving common timeline settings: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


