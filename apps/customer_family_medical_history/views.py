"""
Views for Customer Family Medical History app.
"""

from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Count, Max, Min, Sum
from apps.core.pagination import StandardResultsSetPagination
from .models import CustomerFamilyMedicalHistory
from .serializers import (
    CustomerFamilyMedicalHistorySerializer,
    CustomerFamilyMedicalHistoryCreateSerializer,
    CustomerFamilyMedicalHistoryUpdateSerializer,
    CustomerFamilyMedicalHistoryListSerializer,
    CustomerFamilyMedicalHistoryRiskAssessmentSerializer,
    CustomerFamilyMedicalHistorySummarySerializer
)


class CustomerFamilyMedicalHistoryListCreateView(generics.ListCreateAPIView):
    """
    List all customer family medical history records or create a new one.
    """
    queryset = CustomerFamilyMedicalHistory.objects.filter(is_deleted=False)
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CustomerFamilyMedicalHistoryCreateSerializer
        return CustomerFamilyMedicalHistoryListSerializer
    
    def get_queryset(self):
        queryset = CustomerFamilyMedicalHistory.objects.filter(is_deleted=False)
        
        # Filter by customer
        customer_id = self.request.query_params.get('customer_id')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        
        # Filter by condition category
        condition_category = self.request.query_params.get('condition_category')
        if condition_category:
            queryset = queryset.filter(condition_category=condition_category)
        
        # Filter by condition status
        condition_status = self.request.query_params.get('condition_status')
        if condition_status:
            queryset = queryset.filter(condition_status=condition_status)
        
        # Filter by family relation
        family_relation = self.request.query_params.get('family_relation')
        if family_relation:
            queryset = queryset.filter(family_relation=family_relation)
        
        # Filter by severity level
        severity_level = self.request.query_params.get('severity_level')
        if severity_level:
            queryset = queryset.filter(severity_level=severity_level)
        
        # Filter by insurance impact
        insurance_impact = self.request.query_params.get('insurance_impact')
        if insurance_impact:
            queryset = queryset.filter(insurance_impact=insurance_impact)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by age range
        min_age = self.request.query_params.get('min_age')
        max_age = self.request.query_params.get('max_age')
        if min_age:
            queryset = queryset.filter(age_diagnosed__gte=min_age)
        if max_age:
            queryset = queryset.filter(age_diagnosed__lte=max_age)
        
        # Filter by premium loading range
        min_loading = self.request.query_params.get('min_loading')
        max_loading = self.request.query_params.get('max_loading')
        if min_loading:
            queryset = queryset.filter(premium_loading__gte=min_loading)
        if max_loading:
            queryset = queryset.filter(premium_loading__lte=max_loading)
        
        # Filter by high risk conditions
        high_risk_only = self.request.query_params.get('high_risk_only')
        if high_risk_only and high_risk_only.lower() == 'true':
            # Filter for high risk conditions
            queryset = queryset.filter(
                Q(condition_category__in=['cardiovascular', 'diabetes', 'cancer', 'neurological', 'genetic']) |
                Q(family_relation__in=['self', 'father', 'mother']) |
                Q(severity_level__in=['severe', 'critical'])
            )
        
        # Filter by medical exam required
        medical_exam_required = self.request.query_params.get('medical_exam_required')
        if medical_exam_required and medical_exam_required.lower() == 'true':
            queryset = queryset.filter(
                Q(condition_category__in=['cardiovascular', 'diabetes', 'cancer', 'neurological']) |
                Q(severity_level__in=['severe', 'critical']) |
                Q(family_relation='self')
            )
        
        # Filter by checkup date range
        checkup_from = self.request.query_params.get('checkup_from')
        checkup_to = self.request.query_params.get('checkup_to')
        if checkup_from:
            queryset = queryset.filter(last_checkup_date__gte=checkup_from)
        if checkup_to:
            queryset = queryset.filter(last_checkup_date__lte=checkup_to)
        
        # Search by condition name, doctor name, hospital name, or notes
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(condition_name__icontains=search) |
                Q(doctor_name__icontains=search) |
                Q(hospital_name__icontains=search) |
                Q(notes__icontains=search) |
                Q(current_medication__icontains=search) |
                Q(customer__first_name__icontains=search) |
                Q(customer__last_name__icontains=search) |
                Q(customer__customer_code__icontains=search)
            )
        
        return queryset.select_related('customer').order_by('-created_at')
    
    def perform_create(self, serializer):
        """Create customer family medical history"""
        serializer.save(created_by=self.request.user)


class CustomerFamilyMedicalHistoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete customer family medical history.
    """
    queryset = CustomerFamilyMedicalHistory.objects.filter(is_deleted=False)
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return CustomerFamilyMedicalHistoryUpdateSerializer
        return CustomerFamilyMedicalHistorySerializer
    
    def perform_update(self, serializer):
        """Update customer family medical history"""
        serializer.save(updated_by=self.request.user)
    
    def perform_destroy(self, instance):
        """Soft delete the customer family medical history"""
        instance.delete(user=self.request.user)


@api_view(['GET'])
def customer_medical_history_by_customer(request, customer_id):
    """
    Get all medical history records for a specific customer.
    """
    medical_history = CustomerFamilyMedicalHistory.objects.filter(
        customer_id=customer_id,
        is_deleted=False
    )
    serializer = CustomerFamilyMedicalHistoryListSerializer(medical_history, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def customer_medical_history_risk_assessment(request, customer_id):
    """
    Get risk assessment for a specific customer based on medical history.
    """
    medical_history = CustomerFamilyMedicalHistory.objects.filter(
        customer_id=customer_id,
        is_deleted=False,
        is_active=True
    )
    
    if not medical_history.exists():
        return Response(
            {"detail": "No active medical history found for this customer."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Calculate overall risk assessment
    total_records = medical_history.count()
    high_risk_count = sum(1 for record in medical_history if record.is_high_risk)
    medical_exam_required_count = sum(1 for record in medical_history if record.requires_medical_exam)
    
    # Calculate average risk score
    risk_scores = [record.risk_score for record in medical_history]
    avg_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0
    
    # Calculate total suggested premium loading
    total_premium_loading = sum(
        record.suggested_premium_loading for record in medical_history 
        if record.suggested_premium_loading
    )
    
    # Determine overall risk level
    if high_risk_count >= total_records * 0.5:
        overall_risk_level = 'high'
    elif high_risk_count >= total_records * 0.25:
        overall_risk_level = 'medium'
    else:
        overall_risk_level = 'low'
    
    serializer = CustomerFamilyMedicalHistoryRiskAssessmentSerializer(medical_history, many=True)
    
    return Response({
        'customer_id': customer_id,
        'total_conditions': total_records,
        'high_risk_conditions': high_risk_count,
        'medical_exam_required_conditions': medical_exam_required_count,
        'average_risk_score': round(avg_risk_score, 2),
        'total_suggested_premium_loading': total_premium_loading,
        'overall_risk_level': overall_risk_level,
        'requires_medical_exam': medical_exam_required_count > 0,
        'medical_history_details': serializer.data
    })


@api_view(['GET'])
def medical_history_statistics(request):
    """
    Get statistics about customer family medical history.
    """
    medical_history = CustomerFamilyMedicalHistory.objects.filter(is_deleted=False, is_active=True)
    
    # Condition category distribution
    category_distribution = {}
    for choice in CustomerFamilyMedicalHistory.CONDITION_CATEGORY_CHOICES:
        category_key = choice[0]
        count = medical_history.filter(condition_category=category_key).count()
        category_distribution[category_key] = count
    
    # Family relation distribution
    relation_distribution = {}
    for choice in CustomerFamilyMedicalHistory.FAMILY_RELATION_CHOICES:
        relation_key = choice[0]
        count = medical_history.filter(family_relation=relation_key).count()
        relation_distribution[relation_key] = count
    
    # Severity level distribution
    severity_distribution = {}
    for choice in CustomerFamilyMedicalHistory.SEVERITY_LEVEL_CHOICES:
        severity_key = choice[0]
        count = medical_history.filter(severity_level=severity_key).count()
        severity_distribution[severity_key] = count
    
    # Insurance impact distribution
    impact_distribution = {}
    for choice in CustomerFamilyMedicalHistory.INSURANCE_IMPACT_CHOICES:
        impact_key = choice[0]
        count = medical_history.filter(insurance_impact=impact_key).count()
        impact_distribution[impact_key] = count
    
    # Age distribution
    age_ranges = {
        'child': medical_history.filter(age_diagnosed__lte=12).count(),
        'teen': medical_history.filter(age_diagnosed__gte=13, age_diagnosed__lte=19).count(),
        'young_adult': medical_history.filter(age_diagnosed__gte=20, age_diagnosed__lte=35).count(),
        'middle_age': medical_history.filter(age_diagnosed__gte=36, age_diagnosed__lte=55).count(),
        'senior': medical_history.filter(age_diagnosed__gte=56).count(),
        'unknown': medical_history.filter(age_diagnosed__isnull=True).count(),
    }
    
    # Risk analysis
    high_risk_count = sum(1 for record in medical_history if record.is_high_risk)
    medical_exam_required_count = sum(1 for record in medical_history if record.requires_medical_exam)
    
    # Premium loading analysis
    premium_loading_ranges = {
        'no_loading': medical_history.filter(premium_loading=0).count(),
        'low_loading': medical_history.filter(premium_loading__gt=0, premium_loading__lte=10).count(),
        'medium_loading': medical_history.filter(premium_loading__gt=10, premium_loading__lte=20).count(),
        'high_loading': medical_history.filter(premium_loading__gt=20).count(),
        'no_data': medical_history.filter(premium_loading__isnull=True).count(),
    }
    
    # Aggregate statistics
    aggregates = medical_history.aggregate(
        total_records=Count('id'),
        avg_age_diagnosed=Avg('age_diagnosed'),
        avg_premium_loading=Avg('premium_loading'),
        max_premium_loading=Max('premium_loading'),
        min_premium_loading=Min('premium_loading'),
        total_premium_loading=Sum('premium_loading')
    )
    
    return Response({
        'total_records': aggregates['total_records'],
        'average_age_diagnosed': aggregates['avg_age_diagnosed'],
        'average_premium_loading': aggregates['avg_premium_loading'],
        'max_premium_loading': aggregates['max_premium_loading'],
        'min_premium_loading': aggregates['min_premium_loading'],
        'total_premium_loading': aggregates['total_premium_loading'],
        'high_risk_conditions_count': high_risk_count,
        'medical_exam_required_count': medical_exam_required_count,
        'condition_category_distribution': category_distribution,
        'family_relation_distribution': relation_distribution,
        'severity_level_distribution': severity_distribution,
        'insurance_impact_distribution': impact_distribution,
        'age_distribution': age_ranges,
        'premium_loading_distribution': premium_loading_ranges,
    })


@api_view(['GET'])
def medical_history_summary(request):
    """
    Get summary of all customer medical history for analytics.
    """
    medical_history = CustomerFamilyMedicalHistory.objects.filter(is_deleted=False)
    serializer = CustomerFamilyMedicalHistorySummarySerializer(medical_history, many=True)
    return Response(serializer.data)
