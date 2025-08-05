from rest_framework import serializers
from apps.renewals.models import RenewalCase
from apps.customers.models import Customer
from apps.policies.models import Policy, PolicyType
from apps.channels.models import Channel
from apps.files_upload.models import FileUpload
from django.contrib.auth import get_user_model
from datetime import timedelta

User = get_user_model()

class CaseTrackingSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()
    customer_profile = serializers.SerializerMethodField()
    customer_mobile = serializers.SerializerMethodField()
    customer_language = serializers.SerializerMethodField()
    
    policy_number = serializers.SerializerMethodField()
    product_name = serializers.SerializerMethodField()
    policy_category = serializers.SerializerMethodField()
    renewal_date = serializers.SerializerMethodField()
    policy_status = serializers.SerializerMethodField()
    
    channel_name = serializers.SerializerMethodField()
    
    agent_name = serializers.SerializerMethodField()
    
    upload_date = serializers.SerializerMethodField()
    upload_filename = serializers.SerializerMethodField()
    
    calls_count = serializers.SerializerMethodField()
    last_action = serializers.SerializerMethodField()
    batch_id = serializers.CharField(source='batch_code', read_only=True)
    
    class Meta:
        model = RenewalCase
        fields = [
            'id',
            'case_number',
            'batch_id',
            'status',
            'priority',
            'renewal_amount',
            'payment_status',
            'communication_attempts',
            'last_contact_date',
            'notes',
            'created_at',
            'updated_at',
            'customer_name',
            'customer_profile',
            'customer_mobile',
            'customer_language',
            'policy_number',
            'product_name',
            'policy_category',
            'renewal_date',
            'policy_status',
            'channel_name',
            'agent_name',
            'upload_date',
            'upload_filename',
            'calls_count',
            'last_action',
        ]
    
    def get_customer_name(self, obj):
        return obj.customer.full_name if obj.customer else None
    
    def get_customer_profile(self, obj):
        return obj.customer.profile if obj.customer else None
    
    def get_customer_mobile(self, obj):
        return obj.customer.phone if obj.customer else None
    
    def get_customer_language(self, obj):
        return obj.customer.preferred_language if obj.customer else None
    
    def get_policy_number(self, obj):
        return obj.policy.policy_number if obj.policy else None
    
    def get_product_name(self, obj):
        if obj.policy and obj.policy.policy_type:
            return obj.policy.policy_type.name
        return None
    
    def get_policy_category(self, obj):
        if obj.policy and obj.policy.policy_type:
            return obj.policy.policy_type.category
        return None
    
    def get_renewal_date(self, obj):
        if obj.policy and obj.policy.end_date:
            return obj.policy.end_date.strftime('%d/%m/%Y')
        return None
    
    def get_policy_status(self, obj):
        return obj.policy.status if obj.policy else None
    
    def get_channel_name(self, obj):
        return obj.channel_id.name if obj.channel_id else None
    
    def get_agent_name(self, obj):
        return obj.policy.agent_name if obj.policy and obj.policy.agent_name else None
    
    def get_upload_date(self, obj):
        return obj.created_at.strftime('%d/%m/%Y') if obj.created_at else None
    
    def get_upload_filename(self, obj):
        try:
            time_window = timedelta(minutes=5)
            start_time = obj.created_at - time_window
            end_time = obj.created_at + time_window

            file_upload = FileUpload.objects.filter(
                created_at__range=(start_time, end_time),
                upload_status__in=['completed', 'partial']
            ).order_by('created_at').first()

            return file_upload.original_filename if file_upload else None
        except:
            return None
    
    def get_calls_count(self, obj):
        if obj.communication_attempts:
            return f"{obj.communication_attempts} calls"
        return "0 calls"
    
    def get_last_action(self, obj):
        if obj.last_contact_date:
            return obj.last_contact_date.strftime('%d/%m/%Y')
        elif obj.updated_at:
            return obj.updated_at.strftime('%d/%m/%Y')
        return None


class CaseDetailSerializer(serializers.ModelSerializer):

    batch_id = serializers.CharField(source='batch_code', read_only=True)

    customer_name = serializers.SerializerMethodField()
    customer_code = serializers.SerializerMethodField()
    customer_email = serializers.SerializerMethodField()
    customer_mobile = serializers.SerializerMethodField()
    customer_address = serializers.SerializerMethodField()

    policy_number = serializers.SerializerMethodField()
    policy_type = serializers.SerializerMethodField()
    policy_start_date = serializers.SerializerMethodField()
    policy_end_date = serializers.SerializerMethodField()
    premium_amount = serializers.SerializerMethodField()
    sum_assured = serializers.SerializerMethodField()

    channel_name = serializers.SerializerMethodField()
    agent_name = serializers.SerializerMethodField()

    upload_filename = serializers.SerializerMethodField()
    upload_date = serializers.SerializerMethodField()

    calls_count = serializers.SerializerMethodField()

    class Meta:
        model = RenewalCase
        fields = [
            'id',
            'case_number',
            'batch_id',
            'status',
            'priority',
            'renewal_amount',
            'payment_status',
            'payment_date',
            'communication_attempts',
            'last_contact_date',
            'notes',
            'created_at',
            'updated_at',
            'customer_name',
            'customer_code',
            'customer_email',
            'customer_mobile',
            'customer_address',
            'policy_number',
            'policy_type',
            'policy_start_date',
            'policy_end_date',
            'premium_amount',
            'sum_assured',
            'channel_name',
            'agent_name',
            'upload_filename',
            'upload_date',
            'calls_count',
        ]

    def get_customer_name(self, obj):
        return obj.customer.full_name if obj.customer else None

    def get_customer_code(self, obj):
        return obj.customer.customer_code if obj.customer else None

    def get_customer_email(self, obj):
        return obj.customer.email if obj.customer else None

    def get_customer_mobile(self, obj):
        return obj.customer.phone if obj.customer else None

    def get_customer_address(self, obj):
        if not obj.customer:
            return None
        customer = obj.customer
        address_parts = []
        if customer.address_line1:
            address_parts.append(customer.address_line1)
        if customer.city:
            address_parts.append(customer.city)
        if customer.state:
            address_parts.append(customer.state)
        if customer.postal_code:
            address_parts.append(customer.postal_code)
        return ', '.join(address_parts) if address_parts else None

    def get_policy_number(self, obj):
        return obj.policy.policy_number if obj.policy else None

    def get_policy_type(self, obj):
        return obj.policy.policy_type.name if obj.policy and obj.policy.policy_type else None

    def get_policy_start_date(self, obj):
        return obj.policy.start_date.strftime('%d/%m/%Y') if obj.policy and obj.policy.start_date else None

    def get_policy_end_date(self, obj):
        return obj.policy.end_date.strftime('%d/%m/%Y') if obj.policy and obj.policy.end_date else None

    def get_premium_amount(self, obj):
        return str(obj.policy.premium_amount) if obj.policy and obj.policy.premium_amount else None

    def get_sum_assured(self, obj):
        return str(obj.policy.sum_assured) if obj.policy and obj.policy.sum_assured else None

    def get_channel_name(self, obj):
        return obj.channel_id.name if obj.channel_id else None

    def get_agent_name(self, obj):
        return obj.policy.agent_name if obj.policy and obj.policy.agent_name else None

    def get_upload_filename(self, obj):
        try:

            time_window = timedelta(minutes=5)
            start_time = obj.created_at - time_window
            end_time = obj.created_at + time_window

            file_upload = FileUpload.objects.filter(
                created_at__range=(start_time, end_time),
                upload_status__in=['completed', 'partial']
            ).order_by('created_at').first()

            return file_upload.original_filename if file_upload else None
        except:
            return None

    def get_upload_date(self, obj):
        return obj.created_at.strftime('%d/%m/%Y') if obj.created_at else None

    def get_calls_count(self, obj):
        if obj.communication_attempts:
            return f"{obj.communication_attempts} calls"
        return "0 calls"
