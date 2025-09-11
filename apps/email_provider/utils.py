"""
Utility functions for email provider management
"""
import json
import logging
from cryptography.fernet import Fernet
from django.conf import settings
from django.core.cache import cache
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def get_encryption_key():
    """Get or create encryption key for credentials"""
    key = getattr(settings, 'EMAIL_PROVIDER_ENCRYPTION_KEY', None)
    if not key:
        # In production, this should be set in environment variables
        key = Fernet.generate_key()
        logger.warning("EMAIL_PROVIDER_ENCRYPTION_KEY not set, using generated key")
    return key


def encrypt_credentials(provider_config, credentials: Dict[str, Any]) -> Dict[str, str]:
    """
    Encrypt sensitive credentials for storage
    
    Args:
        provider_config: EmailProviderConfig instance
        credentials: Dictionary of credentials to encrypt
    
    Returns:
        Dictionary with encrypted credentials
    """
    try:
        key = get_encryption_key()
        fernet = Fernet(key)
        
        encrypted_credentials = {}
        
        for field, value in credentials.items():
            if value and field in ['api_key', 'api_secret', 'access_key_id', 'secret_access_key', 'smtp_password']:
                # Encrypt sensitive fields
                encrypted_value = fernet.encrypt(value.encode()).decode()
                encrypted_credentials[field] = encrypted_value
            else:
                encrypted_credentials[field] = value
        
        return encrypted_credentials
        
    except Exception as e:
        logger.error(f"Error encrypting credentials: {str(e)}")
        raise


def decrypt_credentials(provider_config) -> Dict[str, Any]:
    """
    Decrypt credentials for use
    
    Args:
        provider_config: EmailProviderConfig instance
    
    Returns:
        Dictionary with decrypted credentials
    """
    try:
        key = get_encryption_key()
        fernet = Fernet(key)
        
        credentials = {}
        
        # Decrypt sensitive fields
        sensitive_fields = ['api_key', 'api_secret', 'access_key_id', 'secret_access_key', 'smtp_password']
        
        for field in sensitive_fields:
            encrypted_value = getattr(provider_config, field, '')
            if encrypted_value:
                try:
                    decrypted_value = fernet.decrypt(encrypted_value.encode()).decode()
                    credentials[field] = decrypted_value
                except Exception as e:
                    logger.warning(f"Failed to decrypt {field}: {str(e)}")
                    credentials[field] = ''
            else:
                credentials[field] = ''
        
        # Add non-sensitive fields
        non_sensitive_fields = [
            'smtp_host', 'smtp_port', 'smtp_username', 'smtp_use_tls', 'smtp_use_ssl',
            'region', 'from_email', 'from_name', 'reply_to'
        ]
        
        for field in non_sensitive_fields:
            credentials[field] = getattr(provider_config, field, '')
        
        return credentials
        
    except Exception as e:
        logger.error(f"Error decrypting credentials: {str(e)}")
        return {}


def get_provider_cache_key(provider_id: int) -> str:
    """Generate cache key for provider"""
    return f"email_provider_{provider_id}"


def cache_provider_credentials(provider_config, credentials: Dict[str, Any], timeout: int = 3600):
    """
    Cache provider credentials for faster access
    
    Args:
        provider_config: EmailProviderConfig instance
        credentials: Decrypted credentials
        timeout: Cache timeout in seconds
    """
    try:
        cache_key = get_provider_cache_key(provider_config.id)
        cache.set(cache_key, credentials, timeout)
    except Exception as e:
        logger.warning(f"Failed to cache provider credentials: {str(e)}")


def get_cached_provider_credentials(provider_id: int) -> Optional[Dict[str, Any]]:
    """
    Get cached provider credentials
    
    Args:
        provider_id: Provider ID
    
    Returns:
        Cached credentials or None
    """
    try:
        cache_key = get_provider_cache_key(provider_id)
        return cache.get(cache_key)
    except Exception as e:
        logger.warning(f"Failed to get cached provider credentials: {str(e)}")
        return None


def clear_provider_cache(provider_id: int):
    """Clear cached provider credentials"""
    try:
        cache_key = get_provider_cache_key(provider_id)
        cache.delete(cache_key)
    except Exception as e:
        logger.warning(f"Failed to clear provider cache: {str(e)}")


def validate_provider_settings(provider_type: str, settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate provider-specific settings
    
    Args:
        provider_type: Type of provider
        settings: Settings to validate
    
    Returns:
        Dictionary with validation results
    """
    errors = []
    warnings = []
    
    if provider_type == 'sendgrid':
        if not settings.get('api_key'):
            errors.append("API key is required for SendGrid")
        
    elif provider_type == 'aws_ses':
        if not settings.get('access_key_id'):
            errors.append("Access Key ID is required for AWS SES")
        if not settings.get('secret_access_key'):
            errors.append("Secret Access Key is required for AWS SES")
        if not settings.get('region'):
            errors.append("Region is required for AWS SES")
            
    elif provider_type == 'smtp':
        if not settings.get('smtp_host'):
            errors.append("SMTP host is required")
        if not settings.get('smtp_username'):
            errors.append("SMTP username is required")
        if not settings.get('smtp_password'):
            errors.append("SMTP password is required")
    
    # Common validations
    if not settings.get('from_email'):
        errors.append("From email is required")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }


def format_provider_error(error: Exception, provider_name: str) -> str:
    """
    Format provider error messages for logging
    
    Args:
        error: Exception object
        provider_name: Name of the provider
    
    Returns:
        Formatted error message
    """
    error_type = type(error).__name__
    error_message = str(error)
    
    return f"Provider '{provider_name}' error ({error_type}): {error_message}"


def get_provider_priority_list():
    """
    Get list of providers ordered by priority
    
    Returns:
        QuerySet of providers ordered by priority
    """
    from .models import EmailProviderConfig
    
    return EmailProviderConfig.objects.filter(
        is_active=True
    ).order_by('priority', 'name')


def reset_daily_usage():
    """Reset daily usage counters for all providers"""
    from .models import EmailProviderConfig
    from django.utils import timezone
    
    today = timezone.now().date()
    
    providers_to_reset = EmailProviderConfig.objects.filter(
        last_reset_daily__lt=today
    )
    
    for provider in providers_to_reset:
        provider.emails_sent_today = 0
        provider.last_reset_daily = today
        provider.save(update_fields=['emails_sent_today', 'last_reset_daily'])
    
    logger.info(f"Reset daily usage for {providers_to_reset.count()} providers")


def reset_monthly_usage():
    """Reset monthly usage counters for all providers"""
    from .models import EmailProviderConfig
    from django.utils import timezone
    
    today = timezone.now().date()
    
    providers_to_reset = EmailProviderConfig.objects.filter(
        last_reset_monthly__lt=today.replace(day=1)
    )
    
    for provider in providers_to_reset:
        provider.emails_sent_this_month = 0
        provider.last_reset_monthly = today
        provider.save(update_fields=['emails_sent_this_month', 'last_reset_monthly'])
    
    logger.info(f"Reset monthly usage for {providers_to_reset.count()} providers")
