from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.request import Request
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from typing import Any, Dict, Optional, Union, cast
from apps.renewals.models import RenewalCase
from apps.customers.models import Customer
from apps.policies.models import Policy, PolicyType
from apps.case_logs.models import CaseLog
from apps.core.pagination import StandardResultsSetPagination
from .serializers import (
    CaseTrackingSerializer, CaseDetailSerializer, QuickEditCaseSerializer,
    CaseLogSerializer, CaseDetailsSerializer, EditCaseDetailsSerializer
)
from datetime import datetime, timedelta
from django.utils import timezone
from apps.files_upload.models import FileUpload

User = get_user_model()

class CaseTrackingViewSet(viewsets.ReadOnlyModelViewSet):

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    lookup_field = 'id'
    lookup_url_kwarg = 'case_id'
    
    def get_queryset(self):
        return RenewalCase.objects.select_related(
            'customer',                   
            'policy',                      
            'policy__policy_type',       
            'channel_id',                  
            'assigned_to',                 
        ).prefetch_related(
            'customer__policies',          
        ).order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CaseDetailSerializer
        return CaseTrackingSerializer
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'cases': serializer.data,
            'total_count': queryset.count()
        })
    
    def retrieve(self, request, case_id=None, *args, **kwargs):
        queryset = self.get_queryset()
        case = get_object_or_404(queryset, id=case_id)
        serializer = self.get_serializer(case)

        return Response({
            'case': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        queryset = self.get_queryset()
        
        total_cases = queryset.count()
        
        status_stats = {}
        for status_choice in RenewalCase.STATUS_CHOICES:
            status_code = status_choice[0]
            status_label = status_choice[1]
            count = queryset.filter(status=status_code).count()
            status_stats[status_code] = {
                'label': status_label,
                'count': count
            }
        
        priority_stats = {}
        for priority_choice in RenewalCase.PRIORITY_CHOICES:
            priority_code = priority_choice[0]
            priority_label = priority_choice[1]
            count = queryset.filter(priority=priority_code).count()
            priority_stats[priority_code] = {
                'label': priority_label,
                'count': count
            }
        
    
        
        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_cases = queryset.filter(created_at__gte=seven_days_ago).count()
        
        return Response({
            'total_cases': total_cases,
            'status_breakdown': status_stats,
            'priority_breakdown': priority_stats,
            'recent_cases_7_days': recent_cases,
            'generated_at': timezone.now().isoformat()
        })
    
    @action(detail=False, methods=['get'])
    def batch_info(self, request):
        batch_code = request.query_params.get('batch_code')
        
        if batch_code:
            batch_cases = self.get_queryset().filter(batch_code=batch_code)
            
            if not batch_cases.exists():
                return Response(
                    {'error': f'No cases found for batch code: {batch_code}'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            total_cases = batch_cases.count()
            status_breakdown = {}
            
            for status_choice in RenewalCase.STATUS_CHOICES:
                status_code = status_choice[0]
                count = batch_cases.filter(status=status_code).count()
                if count > 0:
                    status_breakdown[status_code] = count
            
            try:
                file_upload = FileUpload.objects.filter(
                    processing_result__batch_code=batch_code
                ).first()
                
                upload_info = None
                if file_upload:
                    upload_info = {
                        'original_filename': file_upload.original_filename,
                        'upload_status': file_upload.upload_status,
                        'total_records': file_upload.total_records,
                        'successful_records': file_upload.successful_records,
                        'failed_records': file_upload.failed_records,
                        'created_at': file_upload.created_at.isoformat()
                    }
            except:
                upload_info = None
            
            return Response({
                'batch_code': batch_code,
                'total_cases': total_cases,
                'status_breakdown': status_breakdown,
                'upload_info': upload_info,
                'cases': CaseTrackingSerializer(batch_cases, many=True).data
            })
        
        else:
            from django.db.models import Count
            
            batch_summary = self.get_queryset().values('batch_code').annotate(
                case_count=Count('id')
            ).order_by('-case_count')
            
            return Response({
                'batches': list(batch_summary),
                'total_batches': len(batch_summary)
            })

    @action(detail=True, methods=['patch'], url_path='quick-edit')
    def quick_edit(self, request, case_id=None):
        return quick_edit_case_api(request, case_id)

    @action(detail=True, methods=['get'], url_path='case-logs')
    def case_logs(self, request, case_id=None):
        """Get all case logs for a specific renewal case"""
        try:
            renewal_case = get_object_or_404(RenewalCase, id=case_id)

            case_logs = CaseLog.objects.filter(
                renewal_case_id=case_id
            ).select_related(
                'renewal_case',
                'renewal_case__customer',
                'renewal_case__policy',
                'created_by',
                'updated_by'
            ).order_by('-created_at')

            page = self.paginate_queryset(case_logs)
            if page is not None:
                serializer = CaseLogSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = CaseLogSerializer(case_logs, many=True)

            return Response({
                'renewal_case': {
                    'id': renewal_case.id,
                    'case_number': renewal_case.case_number,
                    'status': renewal_case.status
                },
                'case_logs': serializer.data,
                'total_logs': case_logs.count()
            })

        except Exception as e:
            return Response({
                'error': 'Failed to retrieve case logs',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='comment-history-formatted')
    def comment_history_formatted(self, request, case_id=None):
        """Get formatted comment history for a case"""
        try:
            renewal_case = get_object_or_404(RenewalCase, id=case_id)

            case_logs = CaseLog.objects.filter(
                renewal_case_id=case_id,
                comment__isnull=False
            ).exclude(comment='').select_related(
                'renewal_case',
                'created_by',
                'updated_by'
            ).order_by('-created_at')

            comment_history = []
            for log in case_logs:
                status_badges = []

                if renewal_case.status:
                    status_badges.append({
                        'type': 'status',
                        'label': renewal_case.get_status_display(),
                        'color': 'orange' if renewal_case.status == 'pending' else 'blue'
                    })

                if log.sub_status:
                    status_badges.append({
                        'type': 'sub_status',
                        'label': log.get_sub_status_display(),
                        'color': 'blue'
                    })

                if log.current_work_step:
                    status_badges.append({
                        'type': 'work_step',
                        'label': f"Step: {log.get_current_work_step_display()}",
                        'color': 'green'
                    })

                if log.next_follow_up_date:
                    status_badges.append({
                        'type': 'follow_up',
                        'label': 'Follow-up Updated',
                        'color': 'yellow'
                    })

                comment_entry = {
                    'id': log.id,
                    'comment': log.comment,
                    'created_by_name': log.created_by.get_full_name() or log.created_by.username if log.created_by else 'Unknown',
                    'created_at': log.created_at.strftime('%m/%d/%Y, %I:%M:%S %p'),
                    'created_at_iso': log.created_at.isoformat(),
                    'next_action_plan': log.next_action_plan or '',
                    'status_badges': status_badges,
                    'sub_status': log.get_sub_status_display(),
                    'work_step': log.get_current_work_step_display(),
                    'next_follow_up_date': log.next_follow_up_date.strftime('%m/%d/%Y') if log.next_follow_up_date else None
                }
                comment_history.append(comment_entry)

            return Response({
                'success': True,
                'renewal_case': {
                    'id': renewal_case.id,
                    'case_number': renewal_case.case_number,
                    'status': renewal_case.status,
                    'status_display': renewal_case.get_status_display()
                },
                'comment_history': comment_history,
                'total_comments': len(comment_history)
            })

        except Exception as e:
            return Response({
                'error': 'Failed to retrieve comment history',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Case Management APIs (moved from case_logs)
@api_view(['PATCH', 'PUT'])
@permission_classes([permissions.IsAuthenticated])
def quick_edit_case_api(request: Union[Request, HttpRequest], case_id: int) -> Response:
    try:
        case = get_object_or_404(
            RenewalCase.objects.select_related('customer', 'policy'),
            id=case_id
        )

        serializer = QuickEditCaseSerializer(data=request.data)  # type: ignore
        if not serializer.is_valid():
            return Response({
                'error': 'Invalid data provided',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data

        with transaction.atomic():
            old_status = case.status
            case.status = validated_data['status']  # type: ignore
            case.updated_by = request.user  # type: ignore
            case.save(update_fields=['status', 'updated_at', 'updated_by'])

            case_log = CaseLog.objects.create(
                renewal_case=case,
                sub_status=validated_data['sub_status'],  # type: ignore
                current_work_step=validated_data['current_work_step'],  # type: ignore
                next_follow_up_date=validated_data.get('next_follow_up_date'),
                next_action_plan=validated_data.get('next_action_plan', ''),
                comment=validated_data.get('comment', ''),
                created_by=request.user,  # type: ignore
                updated_by=request.user  # type: ignore
            )

        return Response({
            'success': True,
            'message': 'Case updated successfully',
            'data': {
                'case_id': case.id,
                'case_number': case.case_number,
                'old_status': old_status,
                'new_status': case.status,
                'case_log_id': case_log.id,
                'sub_status': case_log.get_sub_status_display(),
                'current_work_step': case_log.get_current_work_step_display(),
                'next_follow_up_date': case_log.next_follow_up_date,
                'updated_at': case.updated_at,
                'updated_by': request.user.get_full_name() or request.user.username  # type: ignore
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': 'Failed to update case',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH', 'PUT'])
@permission_classes([permissions.IsAuthenticated])
def update_case_log_api(request: Union[Request, HttpRequest], case_id: int) -> Response:

    try:
        renewal_case = get_object_or_404(
            RenewalCase.objects.select_related('customer', 'policy'),
            id=case_id
        )

        serializer = QuickEditCaseSerializer(data=request.data)  # type: ignore
        if not serializer.is_valid():
            return Response({
                'error': 'Invalid data provided',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data

        with transaction.atomic():
            old_status = renewal_case.status

            renewal_case.status = validated_data['status']  # type: ignore
            renewal_case.updated_by = request.user  # type: ignore
            renewal_case.save(update_fields=['status', 'updated_by', 'updated_at'])

            case_log = CaseLog.objects.create(
                renewal_case=renewal_case,
                sub_status=validated_data['sub_status'],  # type: ignore
                current_work_step=validated_data['current_work_step'],  # type: ignore
                next_follow_up_date=validated_data.get('next_follow_up_date'),
                next_action_plan=validated_data.get('next_action_plan', ''),
                comment=validated_data.get('comment', ''),
                created_by=request.user,  # type: ignore
                updated_by=request.user  # type: ignore
            )

        return Response({
            'success': True,
            'message': 'Case updated successfully',
            'data': {
                'case_id': renewal_case.id,
                'case_number': renewal_case.case_number,
                'old_status': old_status,
                'new_status': renewal_case.status,
                'case_log_id': case_log.id,
                'sub_status': case_log.get_sub_status_display(),
                'current_work_step': case_log.get_current_work_step_display(),
                'next_follow_up_date': case_log.next_follow_up_date,
                'updated_at': renewal_case.updated_at,
                'updated_by': request.user.get_full_name() or request.user.username  # type: ignore
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': 'Failed to update case',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def comment_history_api(request: Union[Request, HttpRequest], case_id: int) -> Response:

    try:
        renewal_case = get_object_or_404(RenewalCase, id=case_id)

        case_logs = CaseLog.objects.filter(
            renewal_case_id=case_id,
            comment__isnull=False
        ).exclude(
            comment=''
        ).select_related(
            'renewal_case',
            'created_by',
            'updated_by'
        ).order_by('-created_at')

        serializer = CaseLogSerializer(case_logs, many=True)

        return Response({
            'success': True,
            'renewal_case': {
                'id': renewal_case.id,
                'case_number': renewal_case.case_number,
                'status': renewal_case.status,
                'status_display': renewal_case.get_status_display()
            },
            'comment_history': serializer.data,
            'total_comments': case_logs.count()
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': 'Failed to retrieve comment history',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_case_details_api(request: Union[Request, HttpRequest], case_id: int) -> Response:
    try:
        renewal_case = get_object_or_404(
            RenewalCase.objects.select_related(
                'customer',
                'policy',
                'policy__policy_type',
                'assigned_to'
            ),
            id=case_id
        )

        serializer = CaseDetailsSerializer(renewal_case)

        return Response({
            'success': True,
            'case_details': serializer.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': 'Failed to fetch case details',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_case_edit_form_data_api(request: Union[Request, HttpRequest], case_id: int) -> Response:
    try:
        renewal_case = get_object_or_404(
            RenewalCase.objects.select_related(
                'customer',
                'policy',
                'policy__policy_type',
                'assigned_to'
            ),
            id=case_id
        )

        policy_types = PolicyType.objects.filter(is_active=True).values('id', 'name', 'category')
        agents = User.objects.filter(is_active=True).values('id', 'first_name', 'last_name', 'email')

        agents_formatted = []
        for agent in agents:
            agents_formatted.append({
                'id': agent['id'],
                'name': f"{agent['first_name']} {agent['last_name']}".strip(),
                'email': agent['email']
            })

        case_serializer = CaseDetailsSerializer(renewal_case)

        return Response({
            'success': True,
            'case_details': case_serializer.data,
            'dropdown_options': {
                'policy_types': list(policy_types),
                'agents': agents_formatted
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': 'Failed to fetch case edit form data',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH'])
@permission_classes([permissions.IsAuthenticated])
def edit_case_details_api(request: Union[Request, HttpRequest], case_id: int) -> Response:
    try:
        renewal_case = get_object_or_404(
            RenewalCase.objects.select_related(
                'customer',
                'policy',
                'policy__policy_type',
                'assigned_to'
            ),
            id=case_id
        )

        serializer = EditCaseDetailsSerializer(data=request.data)  # type: ignore
        if not serializer.is_valid():
            return Response({
                'error': 'Invalid data provided',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data

        with transaction.atomic():
            customer = renewal_case.customer
            customer_updated = False

            if 'customer_name' in validated_data:
                name_parts = validated_data['customer_name'].strip().split(' ', 1)  # type: ignore
                customer.first_name = name_parts[0]
                customer.last_name = name_parts[1] if len(name_parts) > 1 else ''
                customer_updated = True

            if 'email' in validated_data:
                customer.email = validated_data['email']  # type: ignore
                customer_updated = True

            if 'phone' in validated_data:
                customer.phone = validated_data['phone']  # type: ignore
                customer_updated = True

            if customer_updated:
                customer.updated_by = request.user  # type: ignore
                customer.save()

            policy = renewal_case.policy
            policy_updated = False

            if 'policy_type' in validated_data:
                policy_type = PolicyType.objects.get(id=validated_data['policy_type'])  # type: ignore
                policy.policy_type = policy_type
                policy_updated = True

            if 'premium_amount' in validated_data:
                policy.premium_amount = validated_data['premium_amount']  # type: ignore
                policy_updated = True

            if 'expiry_date' in validated_data:
                policy.end_date = validated_data['expiry_date']  # type: ignore
                policy_updated = True

            if 'assigned_agent' in validated_data:
                if validated_data['assigned_agent']:  # type: ignore
                    assigned_agent = get_object_or_404(User, id=validated_data['assigned_agent'])  # type: ignore
                    renewal_case.assigned_to = assigned_agent
                else:
                    renewal_case.assigned_to = None
                renewal_case.updated_by = request.user  # type: ignore
                renewal_case.save(update_fields=['assigned_to', 'updated_by', 'updated_at'])

            if policy_updated:
                policy.last_modified_by = request.user  # type: ignore
                policy.save()

        updated_renewal_case = RenewalCase.objects.select_related(
            'customer',
            'policy',
            'policy__policy_type',
            'assigned_to'
        ).get(id=case_id)

        response_serializer = CaseDetailsSerializer(updated_renewal_case)

        return Response({
            'success': True,
            'message': 'Case details updated successfully',
            'case_details': response_serializer.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': 'Failed to update case details',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_policy_types_dropdown_api(request: Union[Request, HttpRequest]) -> Response:
    try:
        policy_types = PolicyType.objects.filter(is_active=True).values('id', 'name', 'category')

        return Response({
            'success': True,
            'policy_types': list(policy_types)
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': 'Failed to fetch policy types',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_agents_dropdown_api(request: Union[Request, HttpRequest]) -> Response:
    try:
        agents = User.objects.filter(
            is_active=True
        ).values('id', 'first_name', 'last_name', 'username', 'email')

        formatted_agents = []
        for agent in agents:
            full_name = f"{agent['first_name']} {agent['last_name']}".strip()
            if not full_name:
                full_name = agent['username']

            formatted_agents.append({
                'id': agent['id'],
                'name': full_name,
                'username': agent['username'],
                'email': agent['email']
            })

        return Response({
            'success': True,
            'agents': formatted_agents
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': 'Failed to fetch agents',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
