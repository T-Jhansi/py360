"""
API views for Customer Insights endpoints.
"""

from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from datetime import datetime, timedelta

from rest_framework import viewsets
from apps.customers.models import Customer
from .models import (
    CustomerInsight, PaymentInsight, CommunicationInsight, 
    ClaimsInsight, CustomerProfileInsight
)
from .serializers import (
    CustomerInsightsResponseSerializer, PaymentInsightSerializer,
    CommunicationInsightSerializer, ClaimsInsightSerializer,
    CustomerProfileInsightSerializer, PaymentScheduleResponseSerializer,
    PaymentHistoryResponseSerializer, CommunicationHistoryResponseSerializer,
    ClaimsHistoryResponseSerializer, CustomerInsightSerializer,
    CustomerInsightsSummarySerializer, InsightsDashboardSerializer,
    CustomerInsightsFilterSerializer, CustomerInsightsBulkUpdateSerializer
)
from .services import CustomerInsightsService


class CustomerInsightsViewSet(viewsets.ModelViewSet):
    """ViewSet for customer insights operations"""
    
    queryset = CustomerInsight.objects.filter(is_deleted=False)
    serializer_class = CustomerInsightSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        
        # Add customer filtering if needed
        customer_id = self.request.query_params.get('customer_id')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        
        insight_type = self.request.query_params.get('insight_type')
        if insight_type:
            queryset = queryset.filter(insight_type=insight_type)
        
        return queryset.order_by('-calculated_at')
    
    @action(detail=False, methods=['get'], url_path='customer/(?P<customer_id>[^/.]+)')
    def get_customer_insights(self, request, customer_id=None):
        """Get comprehensive insights for a specific customer"""
        try:
            service = CustomerInsightsService()
            insights_data = service.get_customer_insights(int(customer_id))
            
            if 'error' in insights_data:
                return Response(
                    {'error': insights_data['error']}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = CustomerInsightsResponseSerializer(insights_data)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except ValueError:
            return Response(
                {'error': 'Invalid customer ID'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to get customer insights: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='customer/(?P<customer_id>[^/.]+)/payment')
    def get_payment_insights(self, request, customer_id=None):
        """Get payment insights for a specific customer"""
        try:
            customer = Customer.objects.get(id=int(customer_id), is_deleted=False)
            service = CustomerInsightsService()
            payment_insights = service.calculate_payment_insights(customer)
            
            return Response(payment_insights, status=status.HTTP_200_OK)
            
        except Customer.DoesNotExist:
            return Response(
                {'error': 'Customer not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:
            return Response(
                {'error': 'Invalid customer ID'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to get payment insights: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='customer/(?P<customer_id>[^/.]+)/communication')
    def get_communication_insights(self, request, customer_id=None):
        """Get communication insights for a specific customer"""
        try:
            customer = Customer.objects.get(id=int(customer_id), is_deleted=False)
            service = CustomerInsightsService()
            communication_insights = service.calculate_communication_insights(customer)
            
            return Response(communication_insights, status=status.HTTP_200_OK)
            
        except Customer.DoesNotExist:
            return Response(
                {'error': 'Customer not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:
            return Response(
                {'error': 'Invalid customer ID'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to get communication insights: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='customer/(?P<customer_id>[^/.]+)/claims')
    def get_claims_insights(self, request, customer_id=None):
        """Get claims insights for a specific customer"""
        try:
            customer = Customer.objects.get(id=int(customer_id), is_deleted=False)
            service = CustomerInsightsService()
            claims_insights = service.calculate_claims_insights(customer)
            
            return Response(claims_insights, status=status.HTTP_200_OK)
            
        except Customer.DoesNotExist:
            return Response(
                {'error': 'Customer not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:
            return Response(
                {'error': 'Invalid customer ID'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to get claims insights: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='customer/(?P<customer_id>[^/.]+)/payment-schedule')
    def get_payment_schedule(self, request, customer_id=None):
        """Get payment schedule for a specific customer"""
        try:
            customer = Customer.objects.get(id=int(customer_id), is_deleted=False)
            service = CustomerInsightsService()
            payment_schedule = service.get_payment_schedule(customer)
            
            serializer = PaymentScheduleResponseSerializer(payment_schedule)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Customer.DoesNotExist:
            return Response(
                {'error': 'Customer not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:
            return Response(
                {'error': 'Invalid customer ID'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to get payment schedule: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='customer/(?P<customer_id>[^/.]+)/payment-history')
    def get_payment_history(self, request, customer_id=None):
        """Get payment history for a specific customer"""
        try:
            customer = Customer.objects.get(id=int(customer_id), is_deleted=False)
            service = CustomerInsightsService()
            
            years = int(request.query_params.get('years', 10))
            payment_history = service.get_payment_history(customer, years)
            
            serializer = PaymentHistoryResponseSerializer(payment_history)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Customer.DoesNotExist:
            return Response(
                {'error': 'Customer not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:
            return Response(
                {'error': 'Invalid customer ID or years parameter'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to get payment history: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='customer/(?P<customer_id>[^/.]+)/communication-history')
    def get_communication_history(self, request, customer_id=None):
        """Get communication history for a specific customer"""
        try:
            customer = Customer.objects.get(id=int(customer_id), is_deleted=False)
            service = CustomerInsightsService()
            communication_history = service.get_communication_history(customer)
            
            serializer = CommunicationHistoryResponseSerializer(communication_history)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Customer.DoesNotExist:
            return Response(
                {'error': 'Customer not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:
            return Response(
                {'error': 'Invalid customer ID'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to get communication history: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='customer/(?P<customer_id>[^/.]+)/claims-history')
    def get_claims_history(self, request, customer_id=None):
        """Get claims history for a specific customer"""
        try:
            customer = Customer.objects.get(id=int(customer_id), is_deleted=False)
            service = CustomerInsightsService()
            claims_history = service.get_claims_history(customer)
            
            serializer = ClaimsHistoryResponseSerializer(claims_history)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Customer.DoesNotExist:
            return Response(
                {'error': 'Customer not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:
            return Response(
                {'error': 'Invalid customer ID'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to get claims history: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], url_path='bulk-update')
    def bulk_update_insights(self, request):
        """Bulk update insights for multiple customers"""
        serializer = CustomerInsightsBulkUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            customer_ids = serializer.validated_data['customer_ids']
            force_recalculate = serializer.validated_data['force_recalculate']
            
            service = CustomerInsightsService()
            updated_count = 0
            
            for customer_id in customer_ids:
                try:
                    customer = Customer.objects.get(id=customer_id, is_deleted=False)
                    service.get_customer_insights(customer_id)
                    updated_count += 1
                except Customer.DoesNotExist:
                    continue
            
            return Response({
                'message': f'Successfully updated insights for {updated_count} customers',
                'updated_count': updated_count,
                'total_requested': len(customer_ids)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to bulk update insights: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='dashboard')
    def get_insights_dashboard(self, request):
        """Get insights dashboard data"""
        try:
            # Get basic statistics
            total_customers = Customer.objects.filter(is_deleted=False).count()
            
            # High value customers (HNI segment)
            high_value_customers = Customer.objects.filter(
                is_deleted=False,
                profile='HNI'
            ).count()
            
            # Customers with claims (mock data)
            customers_with_claims = 150  # This would be calculated from actual claims data
            
            # Average satisfaction rating
            avg_satisfaction = CommunicationInsight.objects.filter(
                is_deleted=False
            ).aggregate(avg=Avg('satisfaction_rating'))['avg'] or 0.0
            
            # Total premiums collected
            total_premiums = PaymentInsight.objects.filter(
                is_deleted=False
            ).aggregate(total=Sum('total_premiums_paid'))['total'] or 0
            
            # Average payment reliability
            payment_reliability_avg = PaymentInsight.objects.filter(
                is_deleted=False
            ).aggregate(avg=Avg('on_time_payment_rate'))['avg'] or 0.0
            
            # Recent insights (last 10 customers with insights)
            recent_insights = []
            recent_customers = Customer.objects.filter(
                is_deleted=False,
                customer_insights__isnull=False
            ).distinct().order_by('-customer_insights__calculated_at')[:10]
            
            for customer in recent_customers:
                try:
                    payment_insight = PaymentInsight.objects.get(customer=customer, is_deleted=False)
                    communication_insight = CommunicationInsight.objects.get(customer=customer, is_deleted=False)
                    claims_insight = ClaimsInsight.objects.get(customer=customer, is_deleted=False)
                    profile_insight = CustomerProfileInsight.objects.get(customer=customer, is_deleted=False)
                    
                    recent_insights.append({
                        'customer_id': customer.id,
                        'customer_name': customer.full_name,
                        'customer_code': customer.customer_code,
                        'total_premiums_paid': payment_insight.total_premiums_paid,
                        'on_time_payment_rate': payment_insight.on_time_payment_rate,
                        'total_communications': communication_insight.total_communications,
                        'satisfaction_rating': communication_insight.satisfaction_rating,
                        'total_claims': claims_insight.total_claims,
                        'approval_rate': claims_insight.approval_rate,
                        'risk_level': claims_insight.risk_level,
                        'customer_segment': profile_insight.customer_segment,
                        'last_updated': payment_insight.updated_at,
                    })
                except (PaymentInsight.DoesNotExist, CommunicationInsight.DoesNotExist, 
                       ClaimsInsight.DoesNotExist, CustomerProfileInsight.DoesNotExist):
                    continue
            
            dashboard_data = {
                'total_customers': total_customers,
                'high_value_customers': high_value_customers,
                'customers_with_claims': customers_with_claims,
                'avg_satisfaction_rating': round(avg_satisfaction, 1),
                'total_premiums_collected': total_premiums,
                'payment_reliability_avg': round(payment_reliability_avg, 1),
                'recent_insights': recent_insights,
            }
            
            serializer = InsightsDashboardSerializer(dashboard_data)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get dashboard data: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='summary')
    def get_insights_summary(self, request):
        """Get filtered insights summary"""
        filter_serializer = CustomerInsightsFilterSerializer(data=request.query_params)
        if not filter_serializer.is_valid():
            return Response(filter_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            filters = filter_serializer.validated_data
            limit = filters.get('limit', 50)
            offset = filters.get('offset', 0)
            
            # Build query filters
            queryset = Customer.objects.filter(is_deleted=False)
            
            if filters.get('customer_segment'):
                queryset = queryset.filter(
                    customer_insights__profile_insights__customer_segment=filters['customer_segment']
                )
            
            if filters.get('risk_level'):
                queryset = queryset.filter(
                    customer_insights__claims_insights__risk_level=filters['risk_level']
                )
            
            if filters.get('payment_reliability'):
                queryset = queryset.filter(
                    customer_insights__payment_insights__payment_reliability=filters['payment_reliability']
                )
            
            if filters.get('engagement_level'):
                queryset = queryset.filter(
                    customer_insights__communication_insights__engagement_level=filters['engagement_level']
                )
            
            # Apply date filters if provided
            if filters.get('date_from') or filters.get('date_to'):
                date_filter = Q()
                if filters.get('date_from'):
                    date_filter &= Q(customer_insights__calculated_at__gte=filters['date_from'])
                if filters.get('date_to'):
                    date_filter &= Q(customer_insights__calculated_at__lte=filters['date_to'])
                queryset = queryset.filter(date_filter)
            
            # Get paginated results
            customers = queryset.distinct()[offset:offset + limit]
            
            # Build summary data
            summary_data = []
            for customer in customers:
                try:
                    payment_insight = PaymentInsight.objects.get(customer=customer, is_deleted=False)
                    communication_insight = CommunicationInsight.objects.get(customer=customer, is_deleted=False)
                    claims_insight = ClaimsInsight.objects.get(customer=customer, is_deleted=False)
                    profile_insight = CustomerProfileInsight.objects.get(customer=customer, is_deleted=False)
                    
                    summary_data.append({
                        'customer_id': customer.id,
                        'customer_name': customer.full_name,
                        'customer_code': customer.customer_code,
                        'total_premiums_paid': payment_insight.total_premiums_paid,
                        'on_time_payment_rate': payment_insight.on_time_payment_rate,
                        'total_communications': communication_insight.total_communications,
                        'satisfaction_rating': communication_insight.satisfaction_rating,
                        'total_claims': claims_insight.total_claims,
                        'approval_rate': claims_insight.approval_rate,
                        'risk_level': claims_insight.risk_level,
                        'customer_segment': profile_insight.customer_segment,
                        'last_updated': payment_insight.updated_at,
                    })
                except (PaymentInsight.DoesNotExist, CommunicationInsight.DoesNotExist, 
                       ClaimsInsight.DoesNotExist, CustomerProfileInsight.DoesNotExist):
                    continue
            
            return Response({
                'results': summary_data,
                'count': len(summary_data),
                'limit': limit,
                'offset': offset,
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get insights summary: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CustomerInsightsAPIView(APIView):
    """Standalone API view for customer insights"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, customer_id):
        """Get comprehensive customer insights"""
        try:
            service = CustomerInsightsService()
            insights_data = service.get_customer_insights(int(customer_id))
            
            if 'error' in insights_data:
                return Response(
                    {'error': insights_data['error']}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(insights_data, status=status.HTTP_200_OK)
            
        except ValueError:
            return Response(
                {'error': 'Invalid customer ID'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to get customer insights: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request, customer_id):
        """Recalculate insights for a customer"""
        try:
            customer = Customer.objects.get(id=int(customer_id), is_deleted=False)
            service = CustomerInsightsService()
            
            # Force recalculation
            insights_data = service.get_customer_insights(int(customer_id))
            
            return Response({
                'message': 'Insights recalculated successfully',
                'data': insights_data
            }, status=status.HTTP_200_OK)
            
        except Customer.DoesNotExist:
            return Response(
                {'error': 'Customer not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:
            return Response(
                {'error': 'Invalid customer ID'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to recalculate insights: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
