"""
Custom middleware for the Intelipro Insurance Policy Renewal System.
"""

import time
import logging
import json
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from apps.core.models import AuditLog

logger = logging.getLogger(__name__)
User = get_user_model()


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log API requests for auditing and monitoring.
    """
    
    def process_request(self, request):
        """Start timing the request"""
        request.start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Log the request details"""
        try:
            # Calculate request duration
            duration = time.time() - getattr(request, 'start_time', time.time())
            
            # Skip logging for static files and admin
            if (request.path.startswith('/static/') or 
                request.path.startswith('/admin/') or
                request.path.startswith('/media/')):
                return response
            
            # Get user info
            user = request.user if hasattr(request, 'user') and request.user.is_authenticated else None
            
            # Get client IP
            ip_address = self.get_client_ip(request)
            
            # Log API requests
            if request.path.startswith('/api/'):
                log_data = {
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code,
                    'duration': round(duration, 3),
                    'user_id': user.id if user else None,
                    'ip_address': ip_address,
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'content_length': len(response.content) if hasattr(response, 'content') else 0,
                }
                
                # Log request body for POST/PUT/PATCH (excluding sensitive data)
                # Skip body logging for file uploads to avoid "body already read" error
                if (request.method in ['POST', 'PUT', 'PATCH'] and
                    'multipart/form-data' not in request.content_type and
                    'application/octet-stream' not in request.content_type):
                    try:
                        # Only try to read body if it hasn't been read yet
                        if hasattr(request, '_body') and request._body is not None:
                            body = json.loads(request._body.decode('utf-8'))
                            # Remove sensitive fields
                            sensitive_fields = ['password', 'token', 'secret', 'key']
                            for field in sensitive_fields:
                                if field in body:
                                    body[field] = '***REDACTED***'
                            log_data['request_body'] = body
                    except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
                        # Skip logging body if there's any issue reading it
                        pass
                
                # Log to file
                logger.info(f"API Request: {json.dumps(log_data)}")
                
                # Create audit log for important actions
                if (response.status_code < 400 and 
                    request.method in ['POST', 'PUT', 'PATCH', 'DELETE'] and
                    user):
                    
                    action_map = {
                        'POST': 'create',
                        'PUT': 'update',
                        'PATCH': 'update',
                        'DELETE': 'delete',
                    }
                    
                    AuditLog.objects.create(
                        user=user,
                        action=action_map.get(request.method, 'view'),
                        model_name='API',
                        object_repr=request.path,
                        ip_address=ip_address,
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        session_key=request.session.session_key,
                        additional_data={
                            'method': request.method,
                            'status_code': response.status_code,
                            'duration': round(duration, 3),
                        }
                    )
        
        except Exception as e:
            logger.error(f"Error in RequestLoggingMiddleware: {str(e)}")
        
        return response
    
    def get_client_ip(self, request):
        """Get the client's IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class TimezoneMiddleware(MiddlewareMixin):
    """
    Middleware to set timezone based on user preferences.
    """
    
    def process_request(self, request):
        """Set timezone for the request"""
        try:
            if hasattr(request, 'user') and request.user.is_authenticated:
                # Get user's timezone preference
                user_timezone = getattr(request.user, 'timezone', 'UTC')
                timezone.activate(user_timezone)
            else:
                # Check for timezone in headers (for mobile apps)
                client_timezone = request.META.get('HTTP_X_TIMEZONE')
                if client_timezone:
                    timezone.activate(client_timezone)
                else:
                    timezone.deactivate()
        except Exception as e:
            logger.error(f"Error in TimezoneMiddleware: {str(e)}")
            timezone.deactivate()
        
        return None


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add security headers to responses.
    """
    
    def process_response(self, request, response):
        """Add security headers"""
        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' wss: ws:; "
            "frame-ancestors 'none';"
        )
        
        # Other security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "speaker=()"
        )
        
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """
    Simple rate limiting middleware.
    """
    
    def process_request(self, request):
        """Check rate limits"""
        try:
            # Skip rate limiting for certain paths
            if (request.path.startswith('/static/') or 
                request.path.startswith('/admin/') or
                request.path.startswith('/media/')):
                return None
            
            # Get client identifier
            client_id = self.get_client_identifier(request)
            
            # Check rate limit (simplified implementation)
            from django.core.cache import cache
            from django.http import HttpResponse
            
            cache_key = f"rate_limit:{client_id}:{request.path}"
            current_requests = cache.get(cache_key, 0)
            
            # Allow 100 requests per minute per endpoint
            if current_requests >= 100:
                return HttpResponse(
                    json.dumps({
                        'error': 'Rate limit exceeded',
                        'message': 'Too many requests. Please try again later.'
                    }),
                    content_type='application/json',
                    status=429
                )
            
            # Increment counter
            cache.set(cache_key, current_requests + 1, 60)  # 60 seconds
            
        except Exception as e:
            logger.error(f"Error in RateLimitMiddleware: {str(e)}")
        
        return None
    
    def get_client_identifier(self, request):
        """Get client identifier for rate limiting"""
        if hasattr(request, 'user') and request.user.is_authenticated:
            return f"user:{request.user.id}"
        else:
            # Use IP address for anonymous users
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR', 'unknown')
            return f"ip:{ip}" 