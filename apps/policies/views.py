from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.utils.timezone import now
from datetime import date, timedelta
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import (
    PolicyType, Policy, PolicyRenewal, PolicyClaim, 
    PolicyDocument, PolicyBeneficiary, PolicyPayment, PolicyNote
)
from .serializers import (
    PolicyTypeSerializer, PolicySerializer, PolicyListSerializer, PolicyCreateSerializer,
    PolicyRenewalSerializer, PolicyRenewalCreateSerializer,
    PolicyClaimSerializer, PolicyClaimCreateSerializer,
    PolicyDocumentSerializer, PolicyBeneficiarySerializer,
    PolicyPaymentSerializer, PolicyNoteSerializer,
    PolicyDashboardSerializer, RenewalDashboardSerializer
)
from apps.core.pagination import StandardResultsSetPagination

class PolicyTypeViewSet(viewsets.ModelViewSet):
    """ViewSet for managing policy types"""
    queryset = PolicyType.objects.all()
    serializer_class = PolicyTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.query_params.get('active_only'):
            queryset = queryset.filter(is_active=True)
        return queryset

    @action(detail=False, methods=['get'])
    def categories_summary(self, request):
        """Get summary of policy types by category"""
        try:
            policy_types = PolicyType.objects.filter(is_active=True)

            # Group by category
            categories = {}
            for policy_type in policy_types:
                category = policy_type.category
                if category not in categories:
                    categories[category] = []
                categories[category].append({
                    'id': policy_type.id,
                    'name': policy_type.name,
                    'code': policy_type.code,
                    'category': category
                })

            # Count by category
            category_counts = {}
            for category, types in categories.items():
                category_counts[category] = len(types)

            return Response({
                'summary': {
                    'total_policy_types': policy_types.count(),
                    'categories_count': category_counts
                },
                'categories': categories
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': f'Failed to get categories summary: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PolicyViewSet(viewsets.ModelViewSet):
    """ViewSet for managing policies"""
    queryset = Policy.objects.select_related('customer', 'policy_type', 'created_by').prefetch_related(
        'beneficiaries', 'documents', 'payments', 'notes'
    )
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'policy_type', 'customer']
    search_fields = ['policy_number', 'customer__full_name', 'customer__email']
    ordering_fields = ['created_at', 'end_date', 'premium_amount']
    ordering = ['-created_at']
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PolicyListSerializer
        elif self.action == 'create':
            return PolicyCreateSerializer
        return PolicySerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by renewal due
        renewal_due = self.request.query_params.get('renewal_due')
        if renewal_due == 'true':
            thirty_days_from_now = date.today() + timedelta(days=30)
            queryset = queryset.filter(end_date__lte=thirty_days_from_now, status='active')
        
        # Filter by customer
        customer_id = self.request.query_params.get('customer_id')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        serializer.save(last_modified_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get policy dashboard statistics"""
        total_policies = Policy.objects.count()
        active_policies = Policy.objects.filter(status='active').count()
        expired_policies = Policy.objects.filter(status='expired').count()
        
        # Policies due for renewal (within 30 days)
        thirty_days_from_now = date.today() + timedelta(days=30)
        policies_due_for_renewal = Policy.objects.filter(
            end_date__lte=thirty_days_from_now,
            status='active'
        ).count()
        
        # Pending renewals
        pending_renewals = PolicyRenewal.objects.filter(status='pending').count()
        
        # Total premium collected (completed payments)
        total_premium = PolicyPayment.objects.filter(
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Recent claims (last 30 days)
        thirty_days_ago = date.today() - timedelta(days=30)
        recent_claims = PolicyClaim.objects.filter(
            claim_date__gte=thirty_days_ago
        ).count()
        
        data = {
            'total_policies': total_policies,
            'active_policies': active_policies,
            'expired_policies': expired_policies,
            'pending_renewals': pending_renewals,
            'total_premium_collected': total_premium,
            'policies_due_for_renewal': policies_due_for_renewal,
            'recent_claims': recent_claims,
        }
        
        serializer = PolicyDashboardSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def due_for_renewal(self, request):
        """Get policies due for renewal"""
        days = int(request.query_params.get('days', 30))
        target_date = date.today() + timedelta(days=days)
        
        policies = self.get_queryset().filter(
            end_date__lte=target_date,
            status='active'
        )
        
        page = self.paginate_queryset(policies)
        if page is not None:
            serializer = PolicyListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = PolicyListSerializer(policies, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_beneficiary(self, request, pk=None):
        """Add a beneficiary to a policy"""
        policy = self.get_object()
        serializer = PolicyBeneficiarySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(policy=policy)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def add_document(self, request, pk=None):
        """Add a document to a policy"""
        policy = self.get_object()
        serializer = PolicyDocumentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(policy=policy, uploaded_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def add_payment(self, request, pk=None):
        """Add a payment record to a policy"""
        policy = self.get_object()
        serializer = PolicyPaymentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(policy=policy, processed_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def add_note(self, request, pk=None):
        """Add a note to a policy"""
        policy = self.get_object()
        serializer = PolicyNoteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(policy=policy, created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def renewal_dashboard(self, request):
        """Get renewal dashboard statistics with configurable reminder days"""
        today = date.today()

        # Get renewal urgency data using the new method
        urgency_data = Policy.get_policies_by_renewal_urgency()

        # Calculate statistics
        stats = {
            'total_policies': Policy.objects.count(),
            'active_policies': Policy.objects.filter(status='active').count(),
            'expired_policies': Policy.objects.filter(status='expired').count(),
            'renewal_urgency': {
                'overdue': urgency_data['overdue'].count(),
                'due_today': urgency_data['due_today'].count(),
                'due_this_week': urgency_data['due_this_week'].count(),
                'due_this_month': urgency_data['due_this_month'].count(),
            },
            'renewal_reminder_distribution': {}
        }

        # Get renewal reminder days distribution
        reminder_distribution = Policy.objects.values('renewal_reminder_days').annotate(
            count=Count('id')
        ).order_by('renewal_reminder_days')

        for item in reminder_distribution:
            days = item['renewal_reminder_days']
            count = item['count']
            stats['renewal_reminder_distribution'][f'{days}_days'] = count

        return Response(stats)

    @action(detail=False, methods=['post'])
    def configure_renewal_reminders(self, request):
        """Configure renewal reminder days for policies"""
        reminder_days = request.data.get('reminder_days', 30)
        policy_ids = request.data.get('policy_ids', [])
        policy_type = request.data.get('policy_type')
        category = request.data.get('category')

        # Validate reminder_days
        if reminder_days not in [15, 30, 45, 60]:
            return Response(
                {'error': 'reminder_days must be one of: 15, 30, 45, 60'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Build query filters
        filters = {'end_date__isnull': False}

        if policy_ids:
            filters['id__in'] = policy_ids
        elif policy_type:
            filters['policy_type__name__icontains'] = policy_type
        elif category:
            filters['policy_type__category'] = category

        # Get policies to update
        policies_to_update = Policy.objects.filter(**filters)

        if not policies_to_update.exists():
            return Response(
                {'error': 'No policies found matching the criteria'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Update policies
        updated_count = Policy.set_renewal_reminder_days(
            [p.id for p in policies_to_update],
            reminder_days
        )

        return Response({
            'message': f'Successfully updated {updated_count} policies',
            'updated_count': updated_count,
            'reminder_days': reminder_days,
            'filters_applied': {
                'policy_ids': policy_ids if policy_ids else None,
                'policy_type': policy_type,
                'category': category
            }
        })

    @action(detail=False, methods=['get'])
    def renewal_urgency_list(self, request):
        """Get policies by renewal urgency"""
        urgency_type = request.query_params.get('urgency', 'overdue')

        urgency_data = Policy.get_policies_by_renewal_urgency()

        if urgency_type not in urgency_data:
            return Response(
                {'error': 'Invalid urgency type. Choose from: overdue, due_today, due_this_week, due_this_month'},
                status=status.HTTP_400_BAD_REQUEST
            )

        policies = urgency_data[urgency_type]

        page = self.paginate_queryset(policies)
        if page is not None:
            serializer = PolicyListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PolicyListSerializer(policies, many=True)
        return Response({
            'urgency_type': urgency_type,
            'count': policies.count(),
            'policies': serializer.data
        })

    @action(detail=True, methods=['post'])
    def update_renewal_reminder(self, request, pk=None):
        """Update renewal reminder days for a specific policy"""
        policy = self.get_object()
        reminder_days = request.data.get('reminder_days', 30)

        # Validate reminder_days
        if reminder_days not in [15, 30, 45, 60]:
            return Response(
                {'error': 'reminder_days must be one of: 15, 30, 45, 60'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update policy
        old_renewal_date = policy.renewal_date
        policy.renewal_reminder_days = reminder_days
        if policy.end_date:
            policy.renewal_date = policy.end_date - timedelta(days=reminder_days)
        policy.save()

        return Response({
            'message': 'Renewal reminder updated successfully',
            'policy_number': policy.policy_number,
            'old_renewal_date': old_renewal_date,
            'new_renewal_date': policy.renewal_date,
            'reminder_days': reminder_days
        })

    @action(detail=True, methods=['get', 'post'])
    def coverage_details(self, request, pk=None):
        """Get or update coverage details for a policy"""
        policy = self.get_object()

        if request.method == 'GET':
            # Return complete coverage details (policy type + policy specific)
            complete_coverage = policy.get_complete_coverage_details()
            return Response({
                'policy_number': policy.policy_number,
                'policy_type_coverage': policy.policy_type.coverage_details,
                'policy_specific_coverage': policy.coverage_details,
                'complete_coverage': complete_coverage
            })

        elif request.method == 'POST':
            # Update policy-specific coverage details
            coverage_data = request.data.get('coverage_details', {})

            if not isinstance(coverage_data, dict):
                return Response(
                    {'error': 'coverage_details must be a valid JSON object'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            policy.coverage_details = coverage_data
            policy.last_modified_by = request.user
            policy.save()

            return Response({
                'message': 'Coverage details updated successfully',
                'policy_number': policy.policy_number,
                'updated_coverage': policy.coverage_details,
                'complete_coverage': policy.get_complete_coverage_details()
            })

    @action(detail=True, methods=['post'])
    def reset_coverage_to_default(self, request, pk=None):
        """Reset policy coverage details to policy type defaults"""
        policy = self.get_object()

        # Clear policy-specific coverage details
        policy.coverage_details = {}
        policy.last_modified_by = request.user
        policy.save()

        return Response({
            'message': 'Coverage details reset to policy type defaults',
            'policy_number': policy.policy_number,
            'default_coverage': policy.policy_type.coverage_details,
            'complete_coverage': policy.get_complete_coverage_details()
        })

class PolicyRenewalViewSet(viewsets.ModelViewSet):
    """ViewSet for managing policy renewals"""
    queryset = PolicyRenewal.objects.select_related('policy', 'policy__customer', 'assigned_to')
    serializer_class = PolicyRenewalSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'customer_response', 'assigned_to']
    search_fields = ['policy__policy_number', 'policy__customer__full_name']
    ordering_fields = ['renewal_date', 'created_at']
    ordering = ['-renewal_date']
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PolicyRenewalCreateSerializer
        return PolicyRenewalSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by overdue renewals
        overdue = self.request.query_params.get('overdue')
        if overdue == 'true':
            queryset = queryset.filter(
                renewal_date__lt=date.today(),
                status__in=['pending', 'in_progress']
            )
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get renewal dashboard statistics"""
        pending_renewals = PolicyRenewal.objects.filter(status='pending').count()
        in_progress_renewals = PolicyRenewal.objects.filter(status='in_progress').count()
        completed_renewals = PolicyRenewal.objects.filter(status='completed').count()
        
        # Overdue renewals
        overdue_renewals = PolicyRenewal.objects.filter(
            renewal_date__lt=date.today(),
            status__in=['pending', 'in_progress']
        ).count()
        
        # Calculate renewal rate (completed vs total)
        total_renewals = PolicyRenewal.objects.count()
        renewal_rate = (completed_renewals / total_renewals * 100) if total_renewals > 0 else 0
        
        data = {
            'pending_renewals': pending_renewals,
            'in_progress_renewals': in_progress_renewals,
            'completed_renewals': completed_renewals,
            'overdue_renewals': overdue_renewals,
            'renewal_rate': round(renewal_rate, 2),
        }
        
        serializer = RenewalDashboardSerializer(data)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_contacted(self, request, pk=None):
        """Mark renewal as contacted"""
        renewal = self.get_object()
        contact_method = request.data.get('contact_method', '')
        notes = request.data.get('notes', '')
        
        renewal.contact_attempts += 1
        renewal.last_contact_date = timezone.now()
        renewal.contact_method = contact_method
        if notes:
            renewal.notes = notes
        renewal.save()
        
        serializer = self.get_serializer(renewal)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_customer_response(self, request, pk=None):
        """Update customer response for renewal"""
        renewal = self.get_object()
        customer_response = request.data.get('customer_response')
        
        if customer_response in ['interested', 'not_interested', 'needs_time']:
            renewal.customer_response = customer_response
            if customer_response == 'interested':
                renewal.status = 'in_progress'
            elif customer_response == 'not_interested':
                renewal.status = 'cancelled'
            renewal.save()
            
            serializer = self.get_serializer(renewal)
            return Response(serializer.data)
        
        return Response(
            {'error': 'Invalid customer response'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

class PolicyClaimViewSet(viewsets.ModelViewSet):
    """ViewSet for managing policy claims"""
    queryset = PolicyClaim.objects.select_related('policy', 'policy__customer', 'assigned_to')
    serializer_class = PolicyClaimSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'claim_type', 'assigned_to']
    search_fields = ['claim_number', 'policy__policy_number', 'policy__customer__full_name']
    ordering_fields = ['claim_date', 'created_at', 'claim_amount']
    ordering = ['-claim_date']
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PolicyClaimCreateSerializer
        return PolicyClaimSerializer
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a claim"""
        claim = self.get_object()
        approved_amount = request.data.get('approved_amount', claim.claim_amount)
        review_notes = request.data.get('review_notes', '')
        
        claim.status = 'approved'
        claim.approved_amount = approved_amount
        claim.review_notes = review_notes
        claim.save()
        
        serializer = self.get_serializer(claim)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a claim"""
        claim = self.get_object()
        rejection_reason = request.data.get('rejection_reason', '')
        
        claim.status = 'rejected'
        claim.rejection_reason = rejection_reason
        claim.save()
        
        serializer = self.get_serializer(claim)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """Mark claim as paid"""
        claim = self.get_object()
        payment_date = request.data.get('payment_date', date.today())
        payment_reference = request.data.get('payment_reference', '')
        
        claim.status = 'paid'
        claim.payment_date = payment_date
        claim.payment_reference = payment_reference
        claim.save()
        
        serializer = self.get_serializer(claim)
        return Response(serializer.data)

# Additional ViewSets for related models
class PolicyDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing policy documents"""
    queryset = PolicyDocument.objects.select_related('policy', 'uploaded_by', 'verified_by')
    serializer_class = PolicyDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['document_type', 'is_verified']
    search_fields = ['document_name', 'policy__policy_number']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify a document"""
        document = self.get_object()
        document.is_verified = True
        document.verified_by = request.user
        document.verified_at = timezone.now()
        document.save()
        
        serializer = self.get_serializer(document)
        return Response(serializer.data)

class PolicyBeneficiaryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing policy beneficiaries"""
    queryset = PolicyBeneficiary.objects.select_related('policy')
    serializer_class = PolicyBeneficiarySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['is_primary', 'is_active']
    search_fields = ['name', 'policy__policy_number']

class PolicyPaymentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing policy payments"""
    queryset = PolicyPayment.objects.select_related('policy', 'processed_by')
    serializer_class = PolicyPaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'payment_method']
    search_fields = ['transaction_id', 'payment_reference', 'policy__policy_number']
    ordering_fields = ['payment_date', 'amount']
    ordering = ['-payment_date']
    
    def perform_create(self, serializer):
        serializer.save(processed_by=self.request.user)

class PolicyNoteViewSet(viewsets.ModelViewSet):
    """ViewSet for managing policy notes"""
    queryset = PolicyNote.objects.select_related('policy', 'created_by')
    serializer_class = PolicyNoteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['note_type', 'is_customer_visible']
    search_fields = ['note', 'policy__policy_number']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user) 
