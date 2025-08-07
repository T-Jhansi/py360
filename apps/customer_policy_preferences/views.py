"""
Views for Customer Policy Preferences app.
"""

from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Count, Max, Min
from apps.core.pagination import StandardResultsSetPagination
from .models import CustomerPolicyPreference
from .serializers import (
    CustomerPolicyPreferenceSerializer,
    CustomerPolicyPreferenceCreateSerializer,
    CustomerPolicyPreferenceUpdateSerializer,
    CustomerPolicyPreferenceListSerializer,
    CustomerPolicyPreferenceSummarySerializer
)


class CustomerPolicyPreferenceListCreateView(generics.ListCreateAPIView):
    """
    List all customer policy preferences or create a new one.
    """
    queryset = CustomerPolicyPreference.objects.filter(is_deleted=False)
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CustomerPolicyPreferenceCreateSerializer
        return CustomerPolicyPreferenceListSerializer
    
    def get_queryset(self):
        queryset = CustomerPolicyPreference.objects.filter(is_deleted=False)
        
        # Filter by customer
        customer_id = self.request.query_params.get('customer_id')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        
        # Filter by renewal case
        renewal_case_id = self.request.query_params.get('renewal_case_id')
        if renewal_case_id:
            queryset = queryset.filter(renewal_cases_id=renewal_case_id)
        
        # Filter by coverage type
        coverage_type = self.request.query_params.get('coverage_type')
        if coverage_type:
            queryset = queryset.filter(coverage_type=coverage_type)
        
        # Filter by payment mode
        payment_mode = self.request.query_params.get('payment_mode')
        if payment_mode:
            queryset = queryset.filter(payment_mode=payment_mode)
        
        # Filter by preferred insurer
        preferred_insurer = self.request.query_params.get('preferred_insurer')
        if preferred_insurer:
            queryset = queryset.filter(preferred_insurer__icontains=preferred_insurer)
        
        # Filter by tenure range
        min_tenure = self.request.query_params.get('min_tenure')
        max_tenure = self.request.query_params.get('max_tenure')
        if min_tenure:
            queryset = queryset.filter(preferred_tenure__gte=min_tenure)
        if max_tenure:
            queryset = queryset.filter(preferred_tenure__lte=max_tenure)
        
        # Filter by budget range
        min_budget = self.request.query_params.get('min_budget')
        max_budget = self.request.query_params.get('max_budget')
        if min_budget:
            queryset = queryset.filter(budget_range_min__gte=min_budget)
        if max_budget:
            queryset = queryset.filter(budget_range_max__lte=max_budget)
        
        # Filter by auto renewal preference
        auto_renewal = self.request.query_params.get('auto_renewal')
        if auto_renewal is not None:
            queryset = queryset.filter(auto_renewal=auto_renewal.lower() == 'true')
        
        # Filter by digital policy preference
        digital_policy = self.request.query_params.get('digital_policy')
        if digital_policy is not None:
            queryset = queryset.filter(digital_policy=digital_policy.lower() == 'true')
        
        # Filter by communication preference
        communication_preference = self.request.query_params.get('communication_preference')
        if communication_preference:
            queryset = queryset.filter(communication_preference=communication_preference)
        
        # Filter by premium customers
        premium_only = self.request.query_params.get('premium_only')
        if premium_only and premium_only.lower() == 'true':
            # Filter for premium indicators
            queryset = queryset.filter(
                Q(coverage_type__in=['comprehensive', 'premium']) |
                Q(budget_range_max__gt=50000) |
                Q(preferred_tenure__gte=5)
            )
        
        # Filter by created year
        created_year = self.request.query_params.get('created_year')
        if created_year:
            queryset = queryset.filter(created_vy=created_year)
        
        # Search by customer name, code, or insurer
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(customer__first_name__icontains=search) |
                Q(customer__last_name__icontains=search) |
                Q(customer__company_name__icontains=search) |
                Q(customer__customer_code__icontains=search) |
                Q(preferred_insurer__icontains=search) |
                Q(special_requirements__icontains=search)
            )
        
        return queryset.select_related('customer', 'renewal_cases').order_by('-created_at')
    
    def perform_create(self, serializer):
        """Create customer policy preference"""
        serializer.save(created_by=self.request.user)


class CustomerPolicyPreferenceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete customer policy preference.
    """
    queryset = CustomerPolicyPreference.objects.filter(is_deleted=False)
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return CustomerPolicyPreferenceUpdateSerializer
        return CustomerPolicyPreferenceSerializer
    
    def perform_update(self, serializer):
        """Update customer policy preference"""
        serializer.save(updated_by=self.request.user)
    
    def perform_destroy(self, instance):
        """Soft delete the customer policy preference"""
        instance.delete(user=self.request.user)


@api_view(['GET'])
def customer_preferences_by_customer(request, customer_id):
    """
    Get all policy preferences for a specific customer.
    """
    preferences = CustomerPolicyPreference.objects.filter(
        customer_id=customer_id,
        is_deleted=False
    )
    serializer = CustomerPolicyPreferenceListSerializer(preferences, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def customer_preferences_by_renewal_case(request, renewal_case_id):
    """
    Get policy preferences for a specific renewal case.
    """
    try:
        preference = CustomerPolicyPreference.objects.get(
            renewal_cases_id=renewal_case_id,
            is_deleted=False
        )
        serializer = CustomerPolicyPreferenceSerializer(preference)
        return Response(serializer.data)
    except CustomerPolicyPreference.DoesNotExist:
        return Response(
            {"detail": "No preferences found for this renewal case."},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
def customer_preference_statistics(request):
    """
    Get statistics about customer policy preferences.
    """
    preferences = CustomerPolicyPreference.objects.filter(is_deleted=False)
    
    # Coverage type distribution
    coverage_distribution = {}
    for choice in CustomerPolicyPreference.COVERAGE_TYPE_CHOICES:
        coverage_key = choice[0]
        count = preferences.filter(coverage_type=coverage_key).count()
        coverage_distribution[coverage_key] = count
    
    # Payment mode distribution
    payment_distribution = {}
    for choice in CustomerPolicyPreference.PAYMENT_MODE_CHOICES:
        payment_key = choice[0]
        count = preferences.filter(payment_mode=payment_key).count()
        payment_distribution[payment_key] = count
    
    # Tenure distribution
    tenure_ranges = {
        'short_term': preferences.filter(preferred_tenure__lte=2).count(),
        'medium_term': preferences.filter(preferred_tenure__gte=3, preferred_tenure__lte=5).count(),
        'long_term': preferences.filter(preferred_tenure__gte=6).count(),
    }
    
    # Budget distribution
    budget_ranges = {
        'budget': preferences.filter(budget_range_max__lte=25000).count(),
        'mid_range': preferences.filter(budget_range_max__gt=25000, budget_range_max__lte=50000).count(),
        'premium': preferences.filter(budget_range_max__gt=50000).count(),
        'no_budget': preferences.filter(budget_range_max__isnull=True).count(),
    }
    
    # Digital preferences
    digital_stats = {
        'auto_renewal': preferences.filter(auto_renewal=True).count(),
        'digital_policy': preferences.filter(digital_policy=True).count(),
        'email_communication': preferences.filter(communication_preference='email').count(),
        'sms_communication': preferences.filter(communication_preference='sms').count(),
        'whatsapp_communication': preferences.filter(communication_preference='whatsapp').count(),
    }
    
    # Premium customer analysis
    premium_customers = preferences.filter(
        Q(coverage_type__in=['comprehensive', 'premium']) |
        Q(budget_range_max__gt=50000) |
        Q(preferred_tenure__gte=5)
    ).count()
    
    # Preference completeness scores
    preference_scores = [pref.preference_score for pref in preferences]
    score_ranges = {
        'excellent': len([s for s in preference_scores if s >= 80]),
        'good': len([s for s in preference_scores if 60 <= s < 80]),
        'average': len([s for s in preference_scores if 40 <= s < 60]),
        'poor': len([s for s in preference_scores if s < 40]),
    }
    
    # Aggregate statistics
    aggregates = preferences.aggregate(
        total_preferences=Count('id'),
        avg_tenure=Avg('preferred_tenure'),
        avg_budget_min=Avg('budget_range_min'),
        avg_budget_max=Avg('budget_range_max'),
        max_tenure=Max('preferred_tenure'),
        min_tenure=Min('preferred_tenure')
    )
    
    return Response({
        'total_preferences': aggregates['total_preferences'],
        'average_tenure': aggregates['avg_tenure'],
        'average_budget_min': aggregates['avg_budget_min'],
        'average_budget_max': aggregates['avg_budget_max'],
        'max_tenure': aggregates['max_tenure'],
        'min_tenure': aggregates['min_tenure'],
        'premium_customers_count': premium_customers,
        'coverage_type_distribution': coverage_distribution,
        'payment_mode_distribution': payment_distribution,
        'tenure_distribution': tenure_ranges,
        'budget_distribution': budget_ranges,
        'digital_preferences': digital_stats,
        'preference_score_distribution': score_ranges,
    })


@api_view(['GET'])
def customer_preference_summary(request):
    """
    Get summary of all customer preferences for analytics.
    """
    preferences = CustomerPolicyPreference.objects.filter(is_deleted=False)
    serializer = CustomerPolicyPreferenceSummarySerializer(preferences, many=True)
    return Response(serializer.data)
