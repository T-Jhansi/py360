"""
Serializers for Email Provider API endpoints
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import EmailProviderConfig, EmailProviderHealthLog, EmailProviderUsageLog, EmailProviderTestResult
from .utils import validate_provider_settings

User = get_user_model()


class EmailProviderConfigSerializer(serializers.ModelSerializer):
    """Serializer for EmailProviderConfig model"""
    
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    provider_type_display = serializers.CharField(source='get_provider_type_display', read_only=True)
    health_status_display = serializers.CharField(source='get_health_status_display', read_only=True)
    
    # Computed fields
    can_send_email = serializers.SerializerMethodField()
    usage_percentage_daily = serializers.SerializerMethodField()
    usage_percentage_monthly = serializers.SerializerMethodField()
    
    class Meta:
        model = EmailProviderConfig
        fields = [
            'id', 'name', 'provider_type', 'provider_type_display', 'is_default', 'is_active', 'priority',
            'region', 'smtp_host', 'smtp_port', 'smtp_use_tls', 'smtp_use_ssl',
            'from_email', 'from_name', 'reply_to',
            'daily_limit', 'monthly_limit', 'rate_limit_per_minute',
            'last_health_check', 'health_status', 'health_status_display', 'health_error_message',
            'consecutive_failures', 'emails_sent_today', 'emails_sent_this_month',
            'total_emails_sent', 'total_emails_failed', 'average_response_time',
            'can_send_email', 'usage_percentage_daily', 'usage_percentage_monthly',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'last_health_check', 'health_status',
            'health_error_message', 'consecutive_failures', 'emails_sent_today',
            'emails_sent_this_month', 'total_emails_sent', 'total_emails_failed',
            'average_response_time', 'can_send_email', 'usage_percentage_daily',
            'usage_percentage_monthly', 'created_by_name'
        ]
    
    def get_can_send_email(self, obj):
        """Check if provider can send email"""
        can_send, reason = obj.can_send_email()
        return {'can_send': can_send, 'reason': reason}
    
    def get_usage_percentage_daily(self, obj):
        """Calculate daily usage percentage"""
        if obj.daily_limit > 0:
            return round((obj.emails_sent_today / obj.daily_limit) * 100, 2)
        return 0
    
    def get_usage_percentage_monthly(self, obj):
        """Calculate monthly usage percentage"""
        if obj.monthly_limit > 0:
            return round((obj.emails_sent_this_month / obj.monthly_limit) * 100, 2)
        return 0
    
    def validate(self, data):
        """Custom validation"""
        # Validate provider-specific settings
        provider_type = data.get('provider_type')
        if provider_type:
            validation_result = validate_provider_settings(provider_type, data)
            if not validation_result['valid']:
                raise serializers.ValidationError({
                    'provider_settings': validation_result['errors']
                })
        
        # Ensure only one default provider
        if data.get('is_default', False):
            existing_default = EmailProviderConfig.objects.filter(
                is_default=True,
                is_deleted=False
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if existing_default.exists():
                raise serializers.ValidationError({
                    'is_default': 'There is already a default email provider.'
                })
        
        return data
    
    def create(self, validated_data):
        """Create new provider with encrypted credentials"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class EmailProviderConfigCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating EmailProviderConfig with credential handling"""
    
    # Credential fields (not stored directly)
    api_key = serializers.CharField(write_only=True, required=False, allow_blank=True)
    api_secret = serializers.CharField(write_only=True, required=False, allow_blank=True)
    access_key_id = serializers.CharField(write_only=True, required=False, allow_blank=True)
    secret_access_key = serializers.CharField(write_only=True, required=False, allow_blank=True)
    smtp_username = serializers.CharField(write_only=True, required=False, allow_blank=True)
    smtp_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = EmailProviderConfig
        fields = [
            'name', 'provider_type', 'is_default', 'is_active', 'priority',
            'api_key', 'api_secret', 'access_key_id', 'secret_access_key',
            'region', 'smtp_host', 'smtp_port', 'smtp_username', 'smtp_password',
            'smtp_use_tls', 'smtp_use_ssl', 'from_email', 'from_name', 'reply_to',
            'daily_limit', 'monthly_limit', 'rate_limit_per_minute'
        ]
    
    def validate(self, data):
        """Validate provider settings and encrypt credentials"""
        from .utils import encrypt_credentials, validate_provider_settings
        
        provider_type = data.get('provider_type')
        if not provider_type:
            raise serializers.ValidationError({'provider_type': 'Provider type is required'})
        
        # Validate provider-specific settings
        validation_result = validate_provider_settings(provider_type, data)
        if not validation_result['valid']:
            raise serializers.ValidationError({
                'provider_settings': validation_result['errors']
            })
        
        # Encrypt sensitive credentials
        credentials_to_encrypt = {}
        sensitive_fields = ['api_key', 'api_secret', 'access_key_id', 'secret_access_key', 'smtp_password']
        
        for field in sensitive_fields:
            if field in data and data[field]:
                credentials_to_encrypt[field] = data[field]
                # Remove from data to avoid storing plain text
                del data[field]
        
        if credentials_to_encrypt:
            encrypted_credentials = encrypt_credentials(None, credentials_to_encrypt)
            data.update(encrypted_credentials)
        
        return data
    
    def create(self, validated_data):
        """Create provider with encrypted credentials"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class EmailProviderConfigUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating EmailProviderConfig"""
    
    # Credential fields (optional for updates)
    api_key = serializers.CharField(write_only=True, required=False, allow_blank=True)
    api_secret = serializers.CharField(write_only=True, required=False, allow_blank=True)
    access_key_id = serializers.CharField(write_only=True, required=False, allow_blank=True)
    secret_access_key = serializers.CharField(write_only=True, required=False, allow_blank=True)
    smtp_username = serializers.CharField(write_only=True, required=False, allow_blank=True)
    smtp_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = EmailProviderConfig
        fields = [
            'name', 'provider_type', 'is_default', 'is_active', 'priority',
            'api_key', 'api_secret', 'access_key_id', 'secret_access_key',
            'region', 'smtp_host', 'smtp_port', 'smtp_username', 'smtp_password',
            'smtp_use_tls', 'smtp_use_ssl', 'from_email', 'from_name', 'reply_to',
            'daily_limit', 'monthly_limit', 'rate_limit_per_minute'
        ]
    
    def validate(self, data):
        """Validate and encrypt credentials if provided"""
        from .utils import encrypt_credentials, validate_provider_settings
        
        # Only validate if provider_type is being updated
        provider_type = data.get('provider_type', self.instance.provider_type if self.instance else None)
        
        if provider_type:
            # Merge current instance data with new data for validation
            validation_data = {}
            if self.instance:
                validation_data.update({
                    'from_email': self.instance.from_email,
                    'region': self.instance.region,
                    'smtp_host': self.instance.smtp_host,
                    'smtp_port': self.instance.smtp_port,
                    'smtp_username': self.instance.smtp_username,
                })
            validation_data.update(data)
            
            validation_result = validate_provider_settings(provider_type, validation_data)
            if not validation_result['valid']:
                raise serializers.ValidationError({
                    'provider_settings': validation_result['errors']
                })
        
        # Encrypt sensitive credentials if provided
        credentials_to_encrypt = {}
        sensitive_fields = ['api_key', 'api_secret', 'access_key_id', 'secret_access_key', 'smtp_password']
        
        for field in sensitive_fields:
            if field in data and data[field]:
                credentials_to_encrypt[field] = data[field]
                # Remove from data to avoid storing plain text
                del data[field]
        
        if credentials_to_encrypt:
            encrypted_credentials = encrypt_credentials(self.instance, credentials_to_encrypt)
            data.update(encrypted_credentials)
        
        return data


class EmailProviderHealthLogSerializer(serializers.ModelSerializer):
    """Serializer for EmailProviderHealthLog"""
    
    provider_name = serializers.CharField(source='provider.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    test_type_display = serializers.CharField(source='get_test_type_display', read_only=True)
    
    class Meta:
        model = EmailProviderHealthLog
        fields = [
            'id', 'provider', 'provider_name', 'status', 'status_display',
            'response_time', 'error_message', 'test_type', 'test_type_display',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class EmailProviderUsageLogSerializer(serializers.ModelSerializer):
    """Serializer for EmailProviderUsageLog"""
    
    provider_name = serializers.CharField(source='provider.name', read_only=True)
    success_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = EmailProviderUsageLog
        fields = [
            'id', 'provider', 'provider_name', 'emails_sent', 'emails_failed',
            'total_response_time', 'success_rate', 'date'
        ]
        read_only_fields = ['id']
    
    def get_success_rate(self, obj):
        """Calculate success rate percentage"""
        total = obj.emails_sent + obj.emails_failed
        if total > 0:
            return round((obj.emails_sent / total) * 100, 2)
        return 0


class EmailProviderTestResultSerializer(serializers.ModelSerializer):
    """Serializer for EmailProviderTestResult"""
    
    provider_name = serializers.CharField(source='provider.name', read_only=True)
    test_type_display = serializers.CharField(source='get_test_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = EmailProviderTestResult
        fields = [
            'id', 'provider', 'provider_name', 'test_type', 'test_type_display',
            'status', 'status_display', 'message', 'response_time', 'test_data',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class EmailProviderTestSerializer(serializers.Serializer):
    """Serializer for testing email providers"""
    
    test_email = serializers.EmailField(required=False, help_text="Email address to send test to")
    test_type = serializers.ChoiceField(
        choices=['connection', 'authentication', 'send_test', 'api_validation'],
        default='send_test',
        help_text="Type of test to perform"
    )
    
    def validate_test_email(self, value):
        """Validate test email address"""
        if not value:
            # Use provider's from_email as default
            provider = self.context.get('provider')
            if provider:
                credentials = provider.get_encrypted_credentials()
                value = credentials.get('from_email', '')
        
        if not value:
            raise serializers.ValidationError("Test email address is required")
        
        return value


class EmailSendSerializer(serializers.Serializer):
    """Serializer for sending emails through the provider service"""
    
    to_emails = serializers.ListField(
        child=serializers.EmailField(),
        min_length=1,
        help_text="List of recipient email addresses"
    )
    subject = serializers.CharField(max_length=500, help_text="Email subject")
    html_content = serializers.CharField(required=False, allow_blank=True, help_text="HTML email content")
    text_content = serializers.CharField(required=False, allow_blank=True, help_text="Plain text email content")
    from_email = serializers.EmailField(required=False, help_text="From email address")
    from_name = serializers.CharField(max_length=255, required=False, allow_blank=True, help_text="From name")
    reply_to = serializers.EmailField(required=False, help_text="Reply-to email address")
    cc_emails = serializers.ListField(
        child=serializers.EmailField(),
        required=False,
        allow_empty=True,
        help_text="CC email addresses"
    )
    bcc_emails = serializers.ListField(
        child=serializers.EmailField(),
        required=False,
        allow_empty=True,
        help_text="BCC email addresses"
    )
    
    def validate(self, data):
        """Validate email content"""
        html_content = data.get('html_content', '')
        text_content = data.get('text_content', '')
        
        if not html_content and not text_content:
            raise serializers.ValidationError(
                "Either html_content or text_content must be provided"
            )
        
        return data


class EmailProviderStatisticsSerializer(serializers.Serializer):
    """Serializer for email provider statistics"""
    
    provider_name = serializers.CharField()
    provider_type = serializers.CharField()
    is_active = serializers.BooleanField()
    is_default = serializers.BooleanField()
    health_status = serializers.CharField()
    priority = serializers.IntegerField()
    daily_limit = serializers.IntegerField()
    monthly_limit = serializers.IntegerField()
    emails_sent_today = serializers.IntegerField()
    emails_sent_this_month = serializers.IntegerField()
    total_emails_sent = serializers.IntegerField()
    total_emails_failed = serializers.IntegerField()
    average_response_time = serializers.FloatField()
    consecutive_failures = serializers.IntegerField()
    last_health_check = serializers.DateTimeField(allow_null=True)
