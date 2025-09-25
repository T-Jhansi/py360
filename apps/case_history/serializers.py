from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import CaseHistory, CaseComment
from apps.renewals.models import RenewalCase

User = get_user_model()

class CaseCommentSerializer(serializers.ModelSerializer):
    
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    created_by_email = serializers.CharField(source='created_by.email', read_only=True)
    replies_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CaseComment
        fields = [
            'id',
            'comment',
            'comment_type',
            'is_internal',
            'is_important',
            'related_comment',
            'tags',
            'metadata',
            'created_at',
            'created_by',
            'created_by_name',
            'created_by_email',
            'replies_count',
        ]
        read_only_fields = ['id', 'created_at', 'created_by']
    
    def get_replies_count(self, obj):
        """Get count of replies to this comment."""
        return obj.get_replies().count()
    
    def create(self, validated_data):
        """Create a new comment and set the created_by field."""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class CaseHistorySerializer(serializers.ModelSerializer):
    """Serializer for case history entries."""
    
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    created_by_email = serializers.CharField(source='created_by.email', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = CaseHistory
        fields = [
            'id',
            'action',
            'action_display',
            'description',
            'old_value',
            'new_value',
            'related_comment',
            'metadata',
            'created_at',
            'created_by',
            'created_by_name',
            'created_by_email',
        ]
        read_only_fields = ['id', 'created_at', 'created_by']


class CaseSerializer(serializers.ModelSerializer):
    """Serializer for case details with history and comments."""
    
    # Map RenewalCase fields to expected case history fields
    handling_agent_name = serializers.SerializerMethodField()
    case_creation_method = serializers.SerializerMethodField()
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    customer_email = serializers.CharField(source='customer.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    started_at = serializers.DateTimeField(source='created_at', read_only=True)
    closed_at = serializers.SerializerMethodField()
    processing_days = serializers.SerializerMethodField()
    
    # Nested serializers for related data
    history = CaseHistorySerializer(source='case_history', many=True, read_only=True)
    comments = CaseCommentSerializer(source='case_comments', many=True, read_only=True)
    
    # Computed fields
    is_closed = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    
    class Meta:
        model = RenewalCase
        fields = [
            'id',
            'status',
            'status_display',
            'priority',
            'priority_display',
            'handling_agent_name',
            'case_creation_method',
            'customer',
            'customer_name',
            'customer_email',
            'policy',
            'started_at',
            'closed_at',
            'processing_days',
            'renewal_amount',
            'payment_status',
            'batch_code',
            'is_closed',
            'is_active',
            'history',
            'comments',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by',
        ]
    
    # def get_handling_agent(self, obj):
    #     """Get handling agent from policy_agents table"""
    #     if obj.policy and obj.policy.agent:
    #         return f"{obj.policy.agent.agent_name} ({obj.policy.agent.email})"
    #     return None
    
    def get_handling_agent_name(self, obj):
        """Get handling agent name from policy_agents table"""
        if obj.policy and obj.policy.agent:
            return obj.policy.agent.agent_name
        return None
    
    def get_case_creation_method(self, obj):
        """Determine how the case was created based on batch_code"""
        if obj.batch_code:
            return f"Case uploaded via bulk upload (Batch: {obj.batch_code})"
        else:
            return "Case created by agent"
    
    def get_closed_at(self, obj):
        """Get closed date"""
        if obj.status in ['completed', 'renewed', 'cancelled', 'expired']:
            return obj.updated_at
        return None
    
    def get_processing_days(self, obj):
        """Calculate processing days"""
        if obj.created_at:
            from django.utils import timezone
            now = timezone.now()
            if obj.created_at.tzinfo is None:
                # If created_at is naive, make it timezone-aware
                created_at = timezone.make_aware(obj.created_at)
            else:
                created_at = obj.created_at
            delta = now - created_at
            return delta.days
        return 0
    
    def get_is_closed(self, obj):
        """Check if case is closed"""
        return obj.status in ['completed', 'renewed', 'cancelled', 'expired']
    
    def get_is_active(self, obj):
        """Check if case is active"""
        return obj.status not in ['completed', 'renewed', 'cancelled', 'expired']
    
    def create(self, validated_data):
        """Create a new case and set the created_by field."""
        validated_data['created_by'] = self.context['request'].user
        case = super().create(validated_data)
        
        # Create initial history entry
        CaseHistory.objects.create(
            case=case,
            action='case_created',
            description=f"Case {case.case_id} created",
            created_by=self.context['request'].user
        )
        
        return case
    
    def update(self, instance, validated_data):
        """Update case and track changes in history."""
        # Track status changes
        old_status = instance.status
        old_agent = instance.handling_agent
        
        case = super().update(instance, validated_data)
        
        # Create history entries for significant changes
        user = self.context['request'].user
        
        # Status change
        if old_status != case.status:
            CaseHistory.objects.create(
                case=case,
                action='status_changed',
                description=f"Status changed from {old_status} to {case.status}",
                old_value=old_status,
                new_value=case.status,
                created_by=user
            )
        
        # Agent assignment change
        if old_agent != case.handling_agent:
            if case.handling_agent:
                CaseHistory.objects.create(
                    case=case,
                    action='agent_assigned',
                    description=f"Case assigned to {case.handling_agent.get_full_name()}",
                    new_value=str(case.handling_agent.id),
                    created_by=user
                )
            else:
                CaseHistory.objects.create(
                    case=case,
                    action='agent_unassigned',
                    description="Case unassigned from agent",
                    old_value=str(old_agent.id) if old_agent else '',
                    created_by=user
                )
        
        return case


class CaseListSerializer(serializers.ModelSerializer):
    """Simplified serializer for case list views."""
    
    case_id = serializers.CharField(source='case_number', read_only=True)
    title = serializers.SerializerMethodField()
    handling_agent_name = serializers.SerializerMethodField()
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    started_at = serializers.DateTimeField(source='created_at', read_only=True)
    processing_days = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    history_count = serializers.SerializerMethodField()
    
    class Meta:
        model = RenewalCase
        fields = [
            'id',
            'case_id',
            'title',
            'status',
            'status_display',
            'priority',
            'priority_display',
            'handling_agent_name',
            'customer_name',
            'started_at',
            'processing_days',
            'comments_count',
            'history_count',
            'created_at',
        ]
    
    def get_title(self, obj):
        """Get case title from customer and policy info"""
        if obj.customer and obj.policy:
            return f"Renewal for {obj.customer.full_name} - {obj.policy.policy_number}"
        elif obj.customer:
            return f"Renewal for {obj.customer.full_name}"
        else:
            return f"Renewal Case {obj.case_number}"
    
    def get_handling_agent_name(self, obj):
        """Get handling agent name"""
        if obj.assigned_to:
            return obj.assigned_to.get_full_name()
        return None
    
    def get_processing_days(self, obj):
        """Calculate processing days"""
        if obj.created_at:
            from django.utils import timezone
            now = timezone.now()
            if obj.created_at.tzinfo is None:
                created_at = timezone.make_aware(obj.created_at)
            else:
                created_at = obj.created_at
            delta = now - created_at
            return delta.days
        return 0
    
    def get_comments_count(self, obj):
        """Get count of comments for this case."""
        return obj.case_comments.filter(is_deleted=False).count()
    
    def get_history_count(self, obj):
        """Get count of history entries for this case."""
        return obj.case_history.filter(is_deleted=False).count()


class CaseCommentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating case comments."""
    
    class Meta:
        model = CaseComment
        fields = [
            'comment',
            'comment_type',
            'is_internal',
            'is_important',
            'related_comment',
            'tags',
            'metadata',
        ]
    
    def create(self, validated_data):
        """Create a new comment and automatically create history entry."""
        validated_data['created_by'] = self.context['request'].user
        comment = super().create(validated_data)
        
        CaseHistory.objects.create(
            case=comment.case,
            action='comment_added',
            description=f"Comment added: {comment.comment[:100]}{'...' if len(comment.comment) > 100 else ''}",
            related_comment=comment,
            created_by=self.context['request'].user
        )
        
        return comment


class CaseStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating case status."""
    class Meta:
        model = RenewalCase
        fields = ['status']
    
    def update(self, instance, validated_data):
        """Update case status and create history entry."""
        old_status = instance.status
        instance.status = validated_data['status']
        instance.save()
        
        CaseHistory.objects.create(
            case=instance,
            action='status_changed',
            description=f"Status changed from {old_status} to {instance.status}",
            old_value=old_status,
            new_value=instance.status,
            created_by=self.context['request'].user
        )
        
        return instance

class CaseAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for assigning cases to agents."""
    class Meta:
        model = RenewalCase
        fields = ['handling_agent']
    
    def update(self, instance, validated_data):
        """Update case assignment and create history entry."""
        old_agent = instance.handling_agent
        instance.handling_agent = validated_data['handling_agent']
        instance.save()
        
        if instance.handling_agent:
            CaseHistory.objects.create(
                case=instance,
                action='agent_assigned',
                description=f"Case assigned to {instance.handling_agent.get_full_name()}",
                new_value=str(instance.handling_agent.id),
                created_by=self.context['request'].user
            )
        else:
            CaseHistory.objects.create(
                case=instance,
                action='agent_unassigned',
                description="Case unassigned from agent",
                old_value=str(old_agent.id) if old_agent else '',
                created_by=self.context['request'].user
            )
        
        return instance

