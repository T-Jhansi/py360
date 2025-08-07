"""
Policy Timeline views for the Intelipro Insurance Policy Renewal System.
"""

from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import PolicyTimeline
from .serializers import (
    PolicyTimelineSerializer,
    PolicyTimelineDetailSerializer,
    PolicyTimelineCreateSerializer
)
from apps.policies.models import Policy
from apps.customers.models import Customer


class PolicyTimelineListCreateView(generics.ListCreateAPIView):
    """
    List all policy timeline events or create a new timeline event
    """
    queryset = PolicyTimeline.objects.select_related('policy', 'customer', 'agent')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PolicyTimelineCreateSerializer
        return PolicyTimelineSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by policy if provided
        policy_id = self.request.query_params.get('policy_id')
        if policy_id:
            queryset = queryset.filter(policy_id=policy_id)
        
        # Filter by customer if provided
        customer_id = self.request.query_params.get('customer_id')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        
        # Filter by event type if provided
        event_type = self.request.query_params.get('event_type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        # Filter by milestone events only
        milestones_only = self.request.query_params.get('milestones_only')
        if milestones_only and milestones_only.lower() == 'true':
            queryset = queryset.filter(is_milestone=True)
        
        return queryset.filter(is_deleted=False)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class PolicyTimelineDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a policy timeline event
    """
    queryset = PolicyTimeline.objects.select_related('policy', 'customer', 'agent')
    serializer_class = PolicyTimelineDetailSerializer
    lookup_field = 'id'
    
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)
    
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
    
    def perform_destroy(self, instance):
        # Soft delete
        instance.delete(user=self.request.user)


@api_view(['GET'])
def policy_timeline_by_policy(request, policy_id):
    """
    Get timeline events for a specific policy
    """
    try:
        policy = get_object_or_404(Policy, id=policy_id)
        timeline_events = PolicyTimeline.objects.filter(
            policy=policy,
            is_deleted=False
        ).select_related('policy', 'customer', 'agent').order_by('-event_date')
        
        serializer = PolicyTimelineSerializer(timeline_events, many=True)
        
        return Response({
            'success': True,
            'policy_number': policy.policy_number,
            'customer_name': policy.customer.full_name,
            'timeline_events': serializer.data,
            'total_events': timeline_events.count()
        })
    
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def customer_policy_timeline(request, customer_id):
    """
    Get all timeline events for a specific customer across all their policies
    """
    try:
        customer = get_object_or_404(Customer, id=customer_id)
        timeline_events = PolicyTimeline.objects.filter(
            customer=customer,
            is_deleted=False
        ).select_related('policy', 'customer', 'agent').order_by('-event_date')
        
        serializer = PolicyTimelineSerializer(timeline_events, many=True)
        
        return Response({
            'success': True,
            'customer_name': customer.full_name,
            'customer_code': customer.customer_code,
            'timeline_events': serializer.data,
            'total_events': timeline_events.count()
        })
    
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def timeline_event_types(request):
    """
    Get available event types for timeline
    """
    event_types = [
        {'value': choice[0], 'label': choice[1]} 
        for choice in PolicyTimeline.EVENT_TYPE_CHOICES
    ]
    
    event_statuses = [
        {'value': choice[0], 'label': choice[1]} 
        for choice in PolicyTimeline.EVENT_STATUS_CHOICES
    ]
    
    return Response({
        'success': True,
        'event_types': event_types,
        'event_statuses': event_statuses
    })


@api_view(['POST'])
def create_timeline_event(request):
    """
    Create a new timeline event
    """
    try:
        serializer = PolicyTimelineCreateSerializer(data=request.data)
        if serializer.is_valid():
            timeline_event = serializer.save(created_by=request.user)
            
            # Return detailed response
            response_serializer = PolicyTimelineDetailSerializer(timeline_event)
            
            return Response({
                'success': True,
                'message': 'Timeline event created successfully',
                'timeline_event': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
