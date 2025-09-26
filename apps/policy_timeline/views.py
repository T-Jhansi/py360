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
    PolicyTimelineCreateSerializer,
    PolicyTimelineEventSerializer,
    CustomerTimelineSummarySerializer,
    PolicyTimelineFilterSerializer,
    PolicyTimelineDetailViewSerializer,
    PolicyTimelineDashboardSerializer
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


@api_view(['GET'])
def policy_timeline_dashboard(request, customer_id):
    """
    Get comprehensive policy timeline dashboard data for a customer
    """
    try:
        customer = get_object_or_404(Customer, id=customer_id)
        
        # Get timeline events for the customer
        timeline_events = PolicyTimeline.objects.filter(
            customer=customer,
            is_deleted=False
        ).select_related('policy', 'customer', 'agent').order_by('-event_date')
        
        # Get customer summary
        try:
            summary = customer.timeline_summary
        except:
            # Create summary if it doesn't exist
            from .models import CustomerTimelineSummary
            summary = CustomerTimelineSummary.objects.create(
                customer=customer,
                total_events=timeline_events.count(),
                active_policies=customer.policies.filter(status='active').count(),
                total_premium=sum([float(p.premium_amount or 0) for p in customer.policies.filter(status='active')])
            )
        
        # Serialize data
        timeline_serializer = PolicyTimelineDashboardSerializer(timeline_events, many=True)
        summary_serializer = CustomerTimelineSummarySerializer(summary)
        
        return Response({
            'success': True,
            'customer': {
                'id': customer.id,
                'name': customer.full_name,
                'code': customer.customer_code,
            },
            'summary': summary_serializer.data,
            'timeline_events': timeline_serializer.data,
            'total_events': timeline_events.count()
        })
    
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def policy_timeline_complete_view(request, customer_id):
    """
    Get complete policy timeline view with all related customer data
    """
    try:
        customer = get_object_or_404(Customer, id=customer_id)
        
        # Get the most recent timeline event for comprehensive data
        latest_timeline = PolicyTimeline.objects.filter(
            customer=customer,
            is_deleted=False
        ).select_related('policy', 'customer', 'agent').order_by('-event_date').first()
        
        if not latest_timeline:
            return Response({
                'success': False,
                'error': 'No timeline events found for this customer'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Serialize with all related data
        serializer = PolicyTimelineDetailViewSerializer(latest_timeline)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def search_timeline_events(request):
    """
    Search timeline events with filters
    """
    try:
        queryset = PolicyTimeline.objects.select_related('policy', 'customer', 'agent').filter(is_deleted=False)
        
        # Apply filters
        search_query = request.query_params.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(event_title__icontains=search_query) |
                Q(event_description__icontains=search_query) |
                Q(policy__policy_number__icontains=search_query) |
                Q(customer__full_name__icontains=search_query)
            )
        
        # Filter by event type
        event_type = request.query_params.get('event_type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        # Filter by date range
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(event_date__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(event_date__date__lte=end_date)
        
        # Filter by customer
        customer_id = request.query_params.get('customer_id')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        
        # Filter by policy
        policy_id = request.query_params.get('policy_id')
        if policy_id:
            queryset = queryset.filter(policy_id=policy_id)
        
        # Order results
        queryset = queryset.order_by('-event_date')
        
        # Pagination
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size
        
        total_count = queryset.count()
        events = queryset[start:end]
        
        serializer = PolicyTimelineSerializer(events, many=True)
        
        return Response({
            'success': True,
            'results': serializer.data,
            'total_count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size
        })
    
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def timeline_statistics(request):
    """
    Get timeline statistics and analytics
    """
    try:
        from django.db.models import Count, Q
        from django.utils import timezone
        from datetime import timedelta
        
        # Get date range (default to last 30 days)
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Basic statistics
        total_events = PolicyTimeline.objects.filter(is_deleted=False).count()
        recent_events = PolicyTimeline.objects.filter(
            is_deleted=False,
            event_date__gte=start_date
        ).count()
        
        # Events by type
        events_by_type = PolicyTimeline.objects.filter(
            is_deleted=False,
            event_date__gte=start_date
        ).values('event_type').annotate(count=Count('id')).order_by('-count')
        
        # Events by status
        events_by_status = PolicyTimeline.objects.filter(
            is_deleted=False,
            event_date__gte=start_date
        ).values('event_status').annotate(count=Count('id')).order_by('-count')
        
        # Milestone events
        milestone_events = PolicyTimeline.objects.filter(
            is_deleted=False,
            is_milestone=True,
            event_date__gte=start_date
        ).count()
        
        # Follow-up required events
        follow_up_events = PolicyTimeline.objects.filter(
            is_deleted=False,
            follow_up_required=True,
            follow_up_date__gte=timezone.now().date()
        ).count()
        
        return Response({
            'success': True,
            'statistics': {
                'total_events': total_events,
                'recent_events': recent_events,
                'milestone_events': milestone_events,
                'follow_up_events': follow_up_events,
                'events_by_type': list(events_by_type),
                'events_by_status': list(events_by_status),
                'date_range': {
                    'start_date': start_date.date(),
                    'end_date': end_date.date(),
                    'days': days
                }
            }
        })
    
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def create_timeline_event_bulk(request):
    """
    Create multiple timeline events in bulk
    """
    try:
        events_data = request.data.get('events', [])
        if not events_data:
            return Response({
                'success': False,
                'error': 'No events data provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        created_events = []
        errors = []
        
        for event_data in events_data:
            serializer = PolicyTimelineCreateSerializer(data=event_data)
            if serializer.is_valid():
                event = serializer.save(created_by=request.user)
                created_events.append(event)
            else:
                errors.append({
                    'data': event_data,
                    'errors': serializer.errors
                })
        
        response_data = {
            'success': True,
            'created_count': len(created_events),
            'error_count': len(errors),
            'created_events': PolicyTimelineSerializer(created_events, many=True).data
        }
        
        if errors:
            response_data['errors'] = errors
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def policy_timeline_complete_api(request, customer_id):
    """
    COMPLETE POLICY TIMELINE API - Single endpoint for all frontend data
    
    This API provides everything needed for the policy timeline frontend:
    - Customer information
    - Financial profile
    - Family medical history
    - Assets and vehicles
    - Communication preferences
    - Policy preferences
    - Other insurance policies
    - AI insights and recommendations
    - Payment schedules
    - Timeline events with filtering
    - Summary statistics
    
    Query Parameters:
    - search: Search term for timeline events
    - event_type: Filter by event type (creation, renewal, modification, claim, payment, communication)
    - start_date: Filter events from this date (YYYY-MM-DD)
    - end_date: Filter events to this date (YYYY-MM-DD)
    - page: Page number for pagination (default: 1)
    - page_size: Number of events per page (default: 20)
    """
    try:
        customer = get_object_or_404(Customer, id=customer_id)
        
        # Get timeline events with filtering
        timeline_queryset = PolicyTimeline.objects.filter(
            customer=customer,
            is_deleted=False
        ).select_related('policy', 'customer', 'agent').order_by('-event_date')
        
        # Apply search filter
        search_query = request.query_params.get('search', '')
        if search_query:
            timeline_queryset = timeline_queryset.filter(
                Q(event_title__icontains=search_query) |
                Q(event_description__icontains=search_query) |
                Q(policy__policy_number__icontains=search_query)
            )
        
        # Apply event type filter
        event_type = request.query_params.get('event_type')
        if event_type:
            timeline_queryset = timeline_queryset.filter(event_type=event_type)
        
        # Apply date range filters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if start_date:
            timeline_queryset = timeline_queryset.filter(event_date__date__gte=start_date)
        if end_date:
            timeline_queryset = timeline_queryset.filter(event_date__date__lte=end_date)
        
        # Pagination
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size
        
        total_events_count = timeline_queryset.count()
        timeline_events = timeline_queryset[start:end]
        
        # Get or create customer timeline summary
        try:
            summary = customer.timeline_summary
        except:
            from .models import CustomerTimelineSummary
            summary = CustomerTimelineSummary.objects.create(
                customer=customer,
                total_events=total_events_count,
                active_policies=customer.policies.filter(status='active').count(),
                total_premium=sum([float(p.premium_amount or 0) for p in customer.policies.filter(status='active')])
            )
        
        # Serialize all data
        timeline_serializer = PolicyTimelineSerializer(timeline_events, many=True)
        summary_serializer = CustomerTimelineSummarySerializer(summary)
        
        # Get customer's active policies
        active_policies = customer.policies.filter(status='active')
        policies_data = []
        for policy in active_policies:
            policies_data.append({
                'id': policy.id,
                'policy_number': policy.policy_number,
                'policy_type': policy.policy_type.name if policy.policy_type else None,
                'premium_amount': float(policy.premium_amount or 0),
                'start_date': policy.start_date,
                'end_date': policy.end_date,
                'status': policy.status,
                'coverage_amount': float(policy.sum_assured or 0),  # Using sum_assured instead of coverage_amount
            })
        
        # Get financial profile
        financial_profile = None
        try:
            if customer.financial_profile:
                financial_profile = {
                    'annual_income': float(customer.financial_profile.annual_income or 0),
                    'income_captured_date': customer.financial_profile.income_captured_date,
                    'income_source': customer.financial_profile.income_source,
                    'policy_capacity_utilization': customer.financial_profile.policy_capacity_utilization,
                    'recommended_policies_count': customer.financial_profile.recommended_policies_count,
                    'risk_profile': customer.financial_profile.risk_profile,
                    'tolerance_score': float(customer.financial_profile.tolerance_score or 0),
                    'income_range': customer.financial_profile.income_range,
                    'capacity_status': customer.financial_profile.capacity_status,
                }
        except:
            pass
        
        # Get family medical history
        medical_history = []
        try:
            for history in customer.family_medical_history.filter(is_active=True):
                medical_history.append({
                    'condition_name': history.condition_name,
                    'family_relation': history.get_family_relation_display(),
                    'condition_status': history.get_condition_status_display(),
                    'age_diagnosed': history.age_diagnosed,
                    'severity_level': history.get_severity_level_display(),
                    'risk_score': history.risk_score,
                    'is_high_risk': history.is_high_risk,
                })
        except:
            pass
        
        # Get assets and vehicles
        assets_data = []
        vehicles_data = []
        try:
            for asset in customer.assets.all():
                assets_data.append({
                    'residence_type': asset.get_residence_type_display(),
                    'residence_status': asset.get_residence_status_display(),
                    'residence_location': asset.residence_location,
                    'residence_rating': asset.get_residence_rating_display(),
                    'asset_score': asset.asset_score,
                })
                
                # Get vehicles for this asset
                for vehicle in asset.vehicles.all():
                    vehicles_data.append({
                        'vehicle_name': vehicle.vehicle_name,
                        'model_year': vehicle.model_year,
                        'vehicle_type': vehicle.get_vehicle_type_display(),
                        'value': float(vehicle.value),
                        'condition': vehicle.get_condition_display(),
                        'vehicle_age': vehicle.vehicle_age,
                        'vehicle_score': vehicle.vehicle_score,
                    })
        except:
            pass
        
        # Get communication preferences
        communication_preferences = []
        try:
            for pref in customer.detailed_communication_preferences.all():
                communication_preferences.append({
                    'communication_type': pref.get_communication_type_display(),
                    'preferred_channel': pref.get_preferred_channel_display(),
                    'frequency': pref.get_frequency_display(),
                    'email_enabled': pref.email_enabled,
                    'sms_enabled': pref.sms_enabled,
                    'phone_enabled': pref.phone_enabled,
                    'whatsapp_enabled': pref.whatsapp_enabled,
                })
        except:
            pass
        
        # Get policy preferences
        policy_preferences = []
        try:
            for pref in customer.policy_preferences.all():
                policy_preferences.append({
                    'preferred_tenure': pref.preferred_tenure,
                    'coverage_type': pref.get_coverage_type_display(),
                    'preferred_insurer': pref.preferred_insurer,
                    'payment_mode': pref.get_payment_mode_display(),
                    'auto_renewal': pref.auto_renewal,
                    'budget_range_min': float(pref.budget_range_min or 0),
                    'budget_range_max': float(pref.budget_range_max or 0),
                })
        except:
            pass
        
        # Get other insurance policies
        other_policies = []
        try:
            for policy in customer.other_insurance_policies.filter(policy_status='active'):
                other_policies.append({
                    'policy_number': policy.policy_number,
                    'insurance_company': policy.insurance_company,
                    'policy_type': policy.policy_type.name if policy.policy_type else None,
                    'premium_amount': float(policy.premium_amount),
                    'sum_assured': float(policy.sum_assured),
                    'payment_mode': policy.get_payment_mode_display(),
                    'channel': policy.get_channel_display(),
                    'satisfaction_rating': policy.satisfaction_rating,
                    'claim_experience': policy.claim_experience,
                    'switching_potential': policy.switching_potential,
                })
        except:
            pass
        
        # Get AI insights
        ai_insights = []
        try:
            for insight in customer.ai_insights.filter(is_active=True):
                ai_insights.append({
                    'insight_type': insight.get_insight_type_display(),
                    'insight_title': insight.insight_title,
                    'insight_value': insight.insight_value,
                    'insight_description': insight.insight_description,
                    'confidence_score': float(insight.confidence_score or 0),
                    'key_observations': insight.key_observations,
                })
        except:
            pass
        
        # Get AI policy recommendations
        ai_recommendations = []
        try:
            for rec in customer.ai_policy_recommendations.filter(is_active=True):
                ai_recommendations.append({
                    'recommendation_title': rec.recommendation_title,
                    'recommendation_reason': rec.recommendation_reason,
                    'coverage_amount': float(rec.coverage_amount),
                    'estimated_premium': float(rec.estimated_premium),
                    'priority_level': rec.get_priority_level_display(),
                    'recommendation_score': float(rec.recommendation_score or 0),
                    'benefits': rec.benefits,
                    'target_audience': rec.target_audience,
                })
        except:
            pass
        
        # Get payment schedules (if available)
        payment_schedules = []
        try:
            # This would need to be connected through renewal cases
            # For now, return empty list
            pass
        except:
            pass
        
        # Calculate summary statistics
        total_premium = sum([float(p.premium_amount or 0) for p in active_policies])
        total_coverage = sum([float(p.sum_assured or 0) for p in active_policies])  # Using sum_assured instead of coverage_amount
        
        # Get event type counts
        event_type_counts = {}
        for event_type_choice in PolicyTimeline.EVENT_TYPE_CHOICES:
            count = PolicyTimeline.objects.filter(
                customer=customer,
                event_type=event_type_choice[0],
                is_deleted=False
            ).count()
            event_type_counts[event_type_choice[0]] = {
                'label': event_type_choice[1],
                'count': count
            }
        
        return Response({
            'success': True,
            'data': {
                'customer': {
                    'id': customer.id,
                    'name': customer.full_name,
                    'code': customer.customer_code,
                    'email': customer.email,
                    'phone': customer.phone,
                    'date_of_birth': customer.date_of_birth,
                    'gender': customer.gender,
                    'address': f"{customer.address_line1}, {customer.city}, {customer.state}",
                },
                'summary': {
                    'total_events': total_events_count,
                    'active_policies': len(policies_data),
                    'total_premium': total_premium,
                    'total_coverage': total_coverage,
                    'last_activity_date': timeline_events[0].event_date if timeline_events else None,
                },
                'financial_profile': financial_profile,
                'family_medical_history': medical_history,
                'assets': assets_data,
                'vehicles': vehicles_data,
                'communication_preferences': communication_preferences,
                'policy_preferences': policy_preferences,
                'other_insurance_policies': other_policies,
                'ai_insights': ai_insights,
                'ai_policy_recommendations': ai_recommendations,
                'payment_schedules': payment_schedules,
                'active_policies': policies_data,
                'timeline_events': {
                    'results': timeline_serializer.data,
                    'total_count': total_events_count,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (total_events_count + page_size - 1) // page_size,
                    'event_type_counts': event_type_counts,
                },
                'filters': {
                    'search_query': search_query,
                    'event_type': event_type,
                    'start_date': start_date,
                    'end_date': end_date,
                }
            }
        })
    
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
