"""
URL configuration for Intelipro Insurance Policy Renewal System.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from django.http import JsonResponse

# API URL patterns
api_patterns = [
    # Authentication endpoints
    path('auth/', include('apps.authentication.urls')),

    # Core utilities
    path('core/', include('apps.core.urls')),

    # User management
    path('users/', include('apps.users.urls')),

    # Core business endpoints
    path('customers/', include('apps.customers.urls')),
    path('policies/', include('apps.policies.urls')),
    path('campaigns/', include('apps.campaigns.urls')),
    path('templates/', include('apps.templates.urls')),
    path('policy_data/', include('apps.policy_data.urls')),
    path('files_upload/', include('apps.files_upload.urls')),
    path('channels/', include('apps.channels.urls')),
    
    # API Documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Main URL patterns
urlpatterns = [
    # Admin interface
    path(f'{settings.ADMIN_URL if hasattr(settings, "ADMIN_URL") else "admin/"}', admin.site.urls),
    
    # API endpoints
    path('api/', include(api_patterns)),
    
    # Health check endpoint (simple one for now)
    path('health/', lambda request: JsonResponse({'status': 'healthy'})),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Add debug toolbar URLs
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns

# Custom error handlers
handler400 = 'apps.core.views.bad_request'
handler403 = 'apps.core.views.permission_denied'
handler404 = 'apps.core.views.page_not_found'
handler500 = 'apps.core.views.server_error'

# Admin site customization
admin.site.site_header = 'Intelipro Insurance Renewal System'
admin.site.site_title = 'Intelipro Admin'
admin.site.index_title = 'Administration Dashboard' 
