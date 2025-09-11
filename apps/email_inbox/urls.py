"""
Email Inbox URL Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    EmailFolderViewSet, EmailInboxMessageViewSet, EmailConversationViewSet,
    EmailFilterViewSet, EmailSearchQueryViewSet, EmailAttachmentViewSet
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'folders', EmailFolderViewSet, basename='email-folder')
router.register(r'messages', EmailInboxMessageViewSet, basename='email-message')
router.register(r'conversations', EmailConversationViewSet, basename='email-conversation')
router.register(r'filters', EmailFilterViewSet, basename='email-filter')
router.register(r'search-queries', EmailSearchQueryViewSet, basename='email-search-query')
router.register(r'attachments', EmailAttachmentViewSet, basename='email-attachment')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Additional endpoints
    path('receive/', EmailInboxMessageViewSet.as_view({'post': 'create'}), name='email-receive'),
    path('webhook/', EmailInboxMessageViewSet.as_view({'post': 'create'}), name='email-webhook'),
]
