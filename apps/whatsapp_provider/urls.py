from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WhatsAppBusinessAccountViewSet,
    WhatsAppPhoneNumberViewSet,
    WhatsAppMessageTemplateViewSet,
    WhatsAppMessageViewSet,
    WhatsAppWebhookEventViewSet,
    WhatsAppFlowViewSet,
    WhatsAppWebhookView,
    WhatsAppAnalyticsViewSet,
)

# Create router for API endpoints
router = DefaultRouter()
router.register(r'accounts', WhatsAppBusinessAccountViewSet, basename='whatsapp-accounts')
router.register(r'phone-numbers', WhatsAppPhoneNumberViewSet, basename='whatsapp-phone-numbers')
router.register(r'templates', WhatsAppMessageTemplateViewSet, basename='whatsapp-templates')
router.register(r'messages', WhatsAppMessageViewSet, basename='whatsapp-messages')
router.register(r'webhook-events', WhatsAppWebhookEventViewSet, basename='whatsapp-webhook-events')
router.register(r'flows', WhatsAppFlowViewSet, basename='whatsapp-flows')
router.register(r'webhook', WhatsAppWebhookView, basename='whatsapp-webhook')
router.register(r'analytics', WhatsAppAnalyticsViewSet, basename='whatsapp-analytics')

app_name = 'whatsapp_provider'

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
]
