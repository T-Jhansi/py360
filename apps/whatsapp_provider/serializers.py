from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    WhatsAppBusinessAccount,
    WhatsAppPhoneNumber,
    WhatsAppMessageTemplate,
    WhatsAppMessage,
    WhatsAppWebhookEvent,
    WhatsAppFlow,
    WhatsAppAccountHealthLog,
    WhatsAppAccountUsageLog,
)

User = get_user_model()


class WhatsAppPhoneNumberSerializer(serializers.ModelSerializer):
    """Serializer for WhatsApp phone numbers"""
    
    class Meta:
        model = WhatsAppPhoneNumber
        fields = [
            'id', 'phone_number_id', 'phone_number', 'display_phone_number',
            'status', 'is_primary', 'is_active', 'quality_rating',
            'messages_sent_today', 'messages_sent_this_month',
            'last_message_sent', 'created_at', 'updated_at', 'verified_at'
        ]
        read_only_fields = [
            'id', 'phone_number_id', 'messages_sent_today', 'messages_sent_this_month',
            'last_message_sent', 'created_at', 'updated_at', 'verified_at'
        ]


class WhatsAppMessageTemplateSerializer(serializers.ModelSerializer):
    """Serializer for WhatsApp message templates"""
    
    class Meta:
        model = WhatsAppMessageTemplate
        fields = [
            'id', 'name', 'category', 'language', 'header_text', 'body_text',
            'footer_text', 'components', 'status', 'meta_template_id',
            'rejection_reason', 'usage_count', 'last_used',
            'created_at', 'updated_at', 'approved_at'
        ]
        read_only_fields = [
            'id', 'meta_template_id', 'rejection_reason', 'usage_count',
            'last_used', 'created_at', 'updated_at', 'approved_at'
        ]


class WhatsAppBusinessAccountSerializer(serializers.ModelSerializer):
    """Serializer for WhatsApp Business Accounts"""
    
    phone_numbers = WhatsAppPhoneNumberSerializer(many=True, read_only=True)
    message_templates = WhatsAppMessageTemplateSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)
    
    class Meta:
        model = WhatsAppBusinessAccount
        fields = [
            'id', 'name', 'waba_id', 'meta_business_account_id', 'app_id',
            'access_token', 'webhook_verify_token', 'business_name',
            'business_description', 'business_email', 'business_vertical',
            'business_address', 'enable_auto_reply', 'use_knowledge_base',
            'greeting_message', 'fallback_message', 'enable_business_hours',
            'business_hours_start', 'business_hours_end', 'business_timezone',
            'status', 'quality_rating', 'health_status', 'last_health_check',
            'daily_limit', 'monthly_limit', 'rate_limit_per_minute',
            'messages_sent_today', 'messages_sent_this_month',
            'is_default', 'is_active', 'webhook_url', 'subscribed_webhook_events',
            'phone_numbers', 'message_templates', 'created_by_name',
            'updated_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'waba_id', 'messages_sent_today', 'messages_sent_this_month',
            'last_health_check', 'created_at', 'updated_at'
        ]
    
    def validate(self, data):
        """Validate the WhatsApp Business Account data"""
        
        # Validate business hours
        if data.get('enable_business_hours'):
            start_time = data.get('business_hours_start')
            end_time = data.get('business_hours_end')
            
            if start_time and end_time and start_time >= end_time:
                raise serializers.ValidationError({
                    'business_hours_start': 'Start time must be before end time.'
                })
        
        # Validate webhook events
        webhook_events = data.get('subscribed_webhook_events', [])
        valid_events = [
            'messages', 'message_deliveries', 'message_reads',
            'message_template_status_update', 'account_update'
        ]
        
        for event in webhook_events:
            if event not in valid_events:
                raise serializers.ValidationError({
                    'subscribed_webhook_events': f'Invalid webhook event: {event}'
                })
        
        return data


class WhatsAppBusinessAccountCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating WhatsApp Business Accounts"""
    
    class Meta:
        model = WhatsAppBusinessAccount
        fields = [
            'name', 'waba_id', 'meta_business_account_id', 'app_id', 'app_secret',
            'access_token', 'webhook_verify_token', 'business_name',
            'business_description', 'business_email', 'business_vertical',
            'business_address', 'enable_auto_reply', 'use_knowledge_base',
            'greeting_message', 'fallback_message', 'enable_business_hours',
            'business_hours_start', 'business_hours_end', 'business_timezone',
            'daily_limit', 'monthly_limit', 'rate_limit_per_minute',
            'webhook_url', 'subscribed_webhook_events'
        ]
    
    def create(self, validated_data):
        """Create a new WhatsApp Business Account"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class WhatsAppMessageSerializer(serializers.ModelSerializer):
    """Serializer for WhatsApp messages"""
    
    waba_account_name = serializers.CharField(source='waba_account.name', read_only=True)
    phone_number_display = serializers.CharField(source='phone_number.display_phone_number', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True)
    customer_name = serializers.SerializerMethodField()
    
    class Meta:
        model = WhatsAppMessage
        fields = [
            'id', 'message_id', 'direction', 'message_type', 'waba_account',
            'phone_number', 'template', 'to_phone_number', 'from_phone_number',
            'content', 'status', 'error_code', 'error_message', 'campaign',
            'customer', 'metadata', 'waba_account_name', 'phone_number_display',
            'template_name', 'customer_name', 'created_at', 'sent_at',
            'delivered_at', 'read_at'
        ]
        read_only_fields = [
            'id', 'message_id', 'created_at', 'sent_at', 'delivered_at', 'read_at'
        ]
    
    def get_customer_name(self, obj):
        """Get customer full name"""
        if obj.customer:
            return f"{obj.customer.first_name} {obj.customer.last_name}".strip()
        return None


class WhatsAppMessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating WhatsApp messages"""
    
    class Meta:
        model = WhatsAppMessage
        fields = [
            'waba_account', 'phone_number', 'to_phone_number', 'template',
            'message_type', 'content', 'campaign', 'customer', 'metadata'
        ]
    
    def validate(self, data):
        """Validate message creation"""
        waba_account = data.get('waba_account')
        phone_number = data.get('phone_number')
        
        # Validate phone number belongs to WABA account
        if phone_number and waba_account:
            if phone_number.waba_account != waba_account:
                raise serializers.ValidationError({
                    'phone_number': 'Phone number must belong to the selected WABA account.'
                })
        
        # Validate template belongs to WABA account
        template = data.get('template')
        if template and waba_account:
            if template.waba_account != waba_account:
                raise serializers.ValidationError({
                    'template': 'Template must belong to the selected WABA account.'
                })
        
        return data


class WhatsAppWebhookEventSerializer(serializers.ModelSerializer):
    """Serializer for WhatsApp webhook events"""
    
    waba_account_name = serializers.CharField(source='waba_account.name', read_only=True)
    
    class Meta:
        model = WhatsAppWebhookEvent
        fields = [
            'id', 'event_type', 'waba_account', 'message', 'raw_data',
            'processed', 'processing_error', 'waba_account_name',
            'received_at', 'processed_at'
        ]
        read_only_fields = ['id', 'received_at', 'processed_at']


class WhatsAppFlowSerializer(serializers.ModelSerializer):
    """Serializer for WhatsApp Flows"""
    
    waba_account_name = serializers.CharField(source='waba_account.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = WhatsAppFlow
        fields = [
            'id', 'waba_account', 'name', 'description', 'flow_json',
            'status', 'is_active', 'usage_count', 'last_used',
            'waba_account_name', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'usage_count', 'last_used', 'created_at', 'updated_at'
        ]
    
    def create(self, validated_data):
        """Create a new WhatsApp Flow"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class WhatsAppAccountHealthLogSerializer(serializers.ModelSerializer):
    """Serializer for WhatsApp account health logs"""
    
    waba_account_name = serializers.CharField(source='waba_account.name', read_only=True)
    
    class Meta:
        model = WhatsAppAccountHealthLog
        fields = [
            'id', 'waba_account', 'health_status', 'check_details',
            'error_message', 'waba_account_name', 'checked_at'
        ]
        read_only_fields = ['id', 'checked_at']


class WhatsAppAccountUsageLogSerializer(serializers.ModelSerializer):
    """Serializer for WhatsApp account usage logs"""
    
    waba_account_name = serializers.CharField(source='waba_account.name', read_only=True)
    
    class Meta:
        model = WhatsAppAccountUsageLog
        fields = [
            'id', 'waba_account', 'date', 'messages_sent', 'messages_delivered',
            'messages_failed', 'messages_read', 'waba_account_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class WhatsAppAccountSetupSerializer(serializers.Serializer):
    """Serializer for the 6-step WhatsApp account setup process"""
    
    # Step 1: Meta Business Account
    waba_id = serializers.CharField(max_length=50, required=True)
    meta_business_account_id = serializers.CharField(max_length=50, required=True)
    app_id = serializers.CharField(max_length=50, required=False, allow_blank=True)
    app_secret = serializers.CharField(required=False, allow_blank=True)
    
    # Step 2: Phone Number Setup
    phone_number_id = serializers.CharField(max_length=50, required=True)
    phone_number = serializers.CharField(max_length=20, required=True)
    display_phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    
    # Step 3: Access Tokens
    access_token = serializers.CharField(required=True)
    webhook_verify_token = serializers.CharField(max_length=255, required=True)
    
    # Step 4: Business Profile
    business_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    business_description = serializers.CharField(required=False, allow_blank=True)
    business_email = serializers.EmailField(required=False, allow_blank=True)
    business_vertical = serializers.CharField(max_length=100, required=False, allow_blank=True)
    business_address = serializers.CharField(required=False, allow_blank=True)
    
    # Step 5: Bot Configuration
    enable_auto_reply = serializers.BooleanField(default=True)
    use_knowledge_base = serializers.BooleanField(default=True)
    greeting_message = serializers.CharField(default="Hello! I'm your AI assistant. How can I help you today?")
    fallback_message = serializers.CharField(default="I'm sorry, I didn't understand that. Could you please rephrase your question?")
    enable_business_hours = serializers.BooleanField(default=False)
    business_hours_start = serializers.TimeField(default="09:00:00")
    business_hours_end = serializers.TimeField(default="17:00:00")
    business_timezone = serializers.CharField(max_length=50, default="UTC")
    
    # Step 6: Webhook & Review
    webhook_url = serializers.URLField(required=False, allow_blank=True)
    subscribed_webhook_events = serializers.ListField(
        child=serializers.CharField(),
        default=['messages', 'message_deliveries', 'message_reads']
    )
    
    # Account Configuration
    name = serializers.CharField(max_length=100, required=True)
    daily_limit = serializers.IntegerField(default=1000, min_value=1)
    monthly_limit = serializers.IntegerField(default=30000, min_value=1)
    rate_limit_per_minute = serializers.IntegerField(default=10, min_value=1)
    
    def validate_phone_number(self, value):
        """Validate phone number format"""
        if not value.startswith('+'):
            raise serializers.ValidationError("Phone number must include country code (e.g., +1234567890)")
        return value
    
    def validate_subscribed_webhook_events(self, value):
        """Validate webhook events"""
        valid_events = [
            'messages', 'message_deliveries', 'message_reads',
            'message_template_status_update', 'account_update'
        ]
        
        for event in value:
            if event not in valid_events:
                raise serializers.ValidationError(f"Invalid webhook event: {event}")
        
        return value
    
    def create(self, validated_data):
        """Create WhatsApp Business Account and Phone Number"""
        # Extract phone number data
        phone_data = {
            'phone_number_id': validated_data.pop('phone_number_id'),
            'phone_number': validated_data.pop('phone_number'),
            'display_phone_number': validated_data.pop('display_phone_number', ''),
        }
        
        # Create WABA account
        validated_data['created_by'] = self.context['request'].user
        waba_account = WhatsAppBusinessAccount.objects.create(**validated_data)
        
        # Create phone number
        phone_data['waba_account'] = waba_account
        phone_data['is_primary'] = True
        phone_data['status'] = 'verified'  # Assuming verification is done during setup
        WhatsAppPhoneNumber.objects.create(**phone_data)
        
        return waba_account


class WhatsAppMessageSendSerializer(serializers.Serializer):
    """Serializer for sending WhatsApp messages"""
    
    waba_account_id = serializers.IntegerField(required=True)
    to_phone_number = serializers.CharField(max_length=20, required=True)
    message_type = serializers.ChoiceField(choices=[
        ('text', 'Text Message'),
        ('template', 'Template Message'),
        ('interactive', 'Interactive Message'),
    ], default='text')
    
    # For text messages
    text_content = serializers.CharField(required=False, allow_blank=True)
    
    # For template messages
    template_id = serializers.IntegerField(required=False)
    template_params = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    
    # For interactive messages
    flow_id = serializers.IntegerField(required=False)
    flow_token = serializers.CharField(required=False)
    
    # Additional options
    customer_id = serializers.IntegerField(required=False)
    campaign_id = serializers.IntegerField(required=False)
    metadata = serializers.JSONField(required=False, default=dict)
    
    def validate(self, data):
        """Validate message sending data"""
        waba_account_id = data.get('waba_account_id')
        message_type = data.get('message_type')
        
        # Validate WABA account exists and is active
        try:
            waba_account = WhatsAppBusinessAccount.objects.get(
                id=waba_account_id,
                is_active=True,
                status='verified'
            )
        except WhatsAppBusinessAccount.DoesNotExist:
            raise serializers.ValidationError({
                'waba_account_id': 'Invalid or inactive WABA account.'
            })
        
        # Validate message type specific fields
        if message_type == 'text':
            if not data.get('text_content'):
                raise serializers.ValidationError({
                    'text_content': 'Text content is required for text messages.'
                })
        
        elif message_type == 'template':
            if not data.get('template_id'):
                raise serializers.ValidationError({
                    'template_id': 'Template ID is required for template messages.'
                })
            
            # Validate template exists and is approved
            try:
                template = WhatsAppMessageTemplate.objects.get(
                    id=data['template_id'],
                    waba_account=waba_account,
                    status='approved'
                )
                data['template'] = template
            except WhatsAppMessageTemplate.DoesNotExist:
                raise serializers.ValidationError({
                    'template_id': 'Invalid or unapproved template.'
                })
        
        elif message_type == 'interactive':
            if not data.get('flow_id'):
                raise serializers.ValidationError({
                    'flow_id': 'Flow ID is required for interactive messages.'
                })
            
            # Validate flow exists and is active
            try:
                flow = WhatsAppFlow.objects.get(
                    id=data['flow_id'],
                    waba_account=waba_account,
                    is_active=True,
                    status='published'
                )
                data['flow'] = flow
            except WhatsAppFlow.DoesNotExist:
                raise serializers.ValidationError({
                    'flow_id': 'Invalid or inactive flow.'
                })
        
        # Validate phone number format
        to_phone_number = data.get('to_phone_number')
        if not to_phone_number.startswith('+'):
            raise serializers.ValidationError({
                'to_phone_number': 'Phone number must include country code (e.g., +1234567890)'
            })
        
        return data
