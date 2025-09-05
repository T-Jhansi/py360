"""
Serializers for Hierarchy Management API endpoints.
"""

from rest_framework import serializers
from django.db.models import Sum
from .models import HierarchyManagement
from apps.renewals.models import RenewalCase
from apps.users.models import User
import re

class HierarchyManagementSerializer(serializers.ModelSerializer):
    parent_unit_display = serializers.SerializerMethodField()
    cases = serializers.SerializerMethodField()
    revenue = serializers.SerializerMethodField()
    efficiency = serializers.SerializerMethodField()
    
    class Meta:
        model = HierarchyManagement
        fields = [
            'id',
            'unit_name',
            'unit_type',
            'description',
            'parent_unit',
            'parent_unit_display',
            'manager_id',
            'budget',
            'target_cases',
            'status',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by',
            'is_deleted',
            'cases',
            'revenue',
            'efficiency'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'parent_unit_display', 'cases', 'revenue', 'efficiency']
    
    def get_parent_unit_display(self, obj):
        return dict(obj.PARENT_UNIT_CHOICES).get(obj.parent_unit, obj.parent_unit)
    
    def get_cases(self, obj):
        """Get total cases assigned to this hierarchy unit's manager"""
        try:
            manager_number = obj.manager_id.split('-')[1] if '-' in obj.manager_id else obj.manager_id
            user = User.objects.filter(employee_id__icontains=manager_number).first()
            if user:
                return RenewalCase.objects.filter(assigned_to=user).count()
        except (IndexError, AttributeError):
            pass
        return 0
    
    def get_revenue(self, obj):
        """Get total revenue from renewed cases assigned to this hierarchy unit's manager"""
        try:
            manager_number = obj.manager_id.split('-')[1] if '-' in obj.manager_id else obj.manager_id
            user = User.objects.filter(employee_id__icontains=manager_number).first()
            if user:
                result = RenewalCase.objects.filter(
                    assigned_to=user, 
                    status='renewed'
                ).aggregate(total=Sum('renewal_amount'))
                return float(result['total'] or 0)
        except (IndexError, AttributeError):
            pass
        return 0.0
    
    def get_efficiency(self, obj):
        """Calculate efficiency as percentage of renewed cases"""
        try:
            manager_number = obj.manager_id.split('-')[1] if '-' in obj.manager_id else obj.manager_id
            user = User.objects.filter(employee_id__icontains=manager_number).first()
            if user:
                total_cases = RenewalCase.objects.filter(assigned_to=user).count()
                renewed_cases = RenewalCase.objects.filter(assigned_to=user, status='renewed').count()
                if total_cases > 0:
                    return round((renewed_cases / total_cases) * 100, 1)
        except (IndexError, AttributeError):
            pass
        return 0.0


class HierarchyManagementCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = HierarchyManagement
        fields = [
            'unit_name',
            'unit_type',
            'description',
            'parent_unit',
            'manager_id',
            'budget',
            'target_cases',
            'status'
        ]
    
    def validate_parent_unit(self, value):
        valid_choices = [choice[0] for choice in HierarchyManagement.PARENT_UNIT_CHOICES]
        if value not in valid_choices:
            raise serializers.ValidationError(f"Invalid parent unit choice. Must be one of: {valid_choices}")
        return value
    
    def validate_manager_id(self, value):
        if not re.match(r'^mgr-\d{3}$', value):
            raise serializers.ValidationError("Manager ID must be in format mgr-XXX (e.g., mgr-002)")
        return value


class HierarchyManagementListSerializer(serializers.ModelSerializer):

    parent_unit_display = serializers.SerializerMethodField()
    unit_type_display = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    cases = serializers.SerializerMethodField()
    revenue = serializers.SerializerMethodField()
    efficiency = serializers.SerializerMethodField()
    
    class Meta:
        model = HierarchyManagement
        fields = [
            'id',
            'unit_name',
            'unit_type',
            'unit_type_display',
            'parent_unit',
            'parent_unit_display',
            'manager_id',
            'budget',
            'target_cases',
            'status',
            'status_display',
            'created_at',
            'cases',
            'revenue',
            'efficiency'
        ]
    
    def get_parent_unit_display(self, obj):
        return dict(obj.PARENT_UNIT_CHOICES).get(obj.parent_unit, obj.parent_unit)
    
    def get_unit_type_display(self, obj):
        return obj.get_unit_type_display()
    
    def get_status_display(self, obj):
        return obj.get_status_display()
    
    def get_cases(self, obj):
        """Get total cases assigned to this hierarchy unit's manager"""
        try:
            # Extract number from manager_id (e.g., "mgr-001" -> "001")
            manager_number = obj.manager_id.split('-')[1] if '-' in obj.manager_id else obj.manager_id
            # Find user with employee_id matching this pattern (e.g., "EMP001" contains "001")
            user = User.objects.filter(employee_id__icontains=manager_number).first()
            if user:
                return RenewalCase.objects.filter(assigned_to=user).count()
        except (IndexError, AttributeError):
            pass
        return 0
    
    def get_revenue(self, obj):
        """Get total revenue from renewed cases assigned to this hierarchy unit's manager"""
        try:
            # Extract number from manager_id (e.g., "mgr-001" -> "001")
            manager_number = obj.manager_id.split('-')[1] if '-' in obj.manager_id else obj.manager_id
            # Find user with employee_id matching this pattern (e.g., "EMP001" contains "001")
            user = User.objects.filter(employee_id__icontains=manager_number).first()
            if user:
                result = RenewalCase.objects.filter(
                    assigned_to=user, 
                    status='renewed'
                ).aggregate(total=Sum('renewal_amount'))
                return float(result['total'] or 0)
        except (IndexError, AttributeError):
            pass
        return 0.0
    
    def get_efficiency(self, obj):
        """Calculate efficiency as percentage of renewed cases"""
        try:
            # Extract number from manager_id (e.g., "mgr-001" -> "001")
            manager_number = obj.manager_id.split('-')[1] if '-' in obj.manager_id else obj.manager_id
            # Find user with employee_id matching this pattern (e.g., "EMP001" contains "001")
            user = User.objects.filter(employee_id__icontains=manager_number).first()
            if user:
                total_cases = RenewalCase.objects.filter(assigned_to=user).count()
                renewed_cases = RenewalCase.objects.filter(assigned_to=user, status='renewed').count()
                if total_cases > 0:
                    return round((renewed_cases / total_cases) * 100, 1)
        except (IndexError, AttributeError):
            pass
        return 0.0
