"""
Serializers for Hierarchy Management API endpoints.
"""

from rest_framework import serializers
from .models import HierarchyManagement
import re

class HierarchyManagementSerializer(serializers.ModelSerializer):
    parent_unit_display = serializers.SerializerMethodField()
    
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
            'is_deleted'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'parent_unit_display']
    
    def get_parent_unit_display(self, obj):
        return dict(obj.PARENT_UNIT_CHOICES).get(obj.parent_unit, obj.parent_unit)


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
            'created_at'
        ]
    
    def get_parent_unit_display(self, obj):
        return dict(obj.PARENT_UNIT_CHOICES).get(obj.parent_unit, obj.parent_unit)
    
    def get_unit_type_display(self, obj):
        return obj.get_unit_type_display()
    
    def get_status_display(self, obj):
        return obj.get_status_display()
