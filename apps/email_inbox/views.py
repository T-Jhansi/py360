"""
Email Inbox API Views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import models
from django.shortcuts import get_object_or_404
from django.utils import timezone
from typing import Dict, Any

from .models import (
    EmailInboxMessage, EmailConversation, EmailFolder, EmailFilter,
    EmailAttachment, EmailSearchQuery
)
from .serializers import (
    EmailInboxMessageSerializer, EmailInboxMessageCreateSerializer,
    EmailConversationSerializer, EmailFolderSerializer, EmailFilterSerializer,
    EmailAttachmentSerializer, EmailSearchQuerySerializer,
    EmailBulkActionSerializer, EmailSearchSerializer, EmailReplySerializer,
    EmailForwardSerializer, EmailStatsSerializer
)
from .services import email_inbox_service


class EmailFolderViewSet(viewsets.ModelViewSet):
    """ViewSet for managing email folders"""
    
    queryset = EmailFolder.objects.all()
    serializer_class = EmailFolderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter folders based on user permissions"""
        return EmailFolder.objects.all().order_by('sort_order', 'name')
    
    @action(detail=False, methods=['get'])
    def system_folders(self, request):
        """Get system folders"""
        folders = EmailFolder.objects.filter(is_system=True).order_by('sort_order')
        serializer = self.get_serializer(folders, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def custom_folders(self, request):
        """Get custom folders"""
        folders = EmailFolder.objects.filter(is_system=False).order_by('sort_order')
        serializer = self.get_serializer(folders, many=True)
        return Response(serializer.data)


class EmailInboxMessageViewSet(viewsets.ModelViewSet):
    """ViewSet for managing email inbox messages"""
    
    queryset = EmailInboxMessage.objects.filter(is_deleted=False)
    serializer_class = EmailInboxMessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return EmailInboxMessageCreateSerializer
        return EmailInboxMessageSerializer
    
    def get_queryset(self):
        """Filter messages based on query parameters"""
        queryset = EmailInboxMessage.objects.filter(is_deleted=False)
        
        # Apply filters
        folder_id = self.request.query_params.get('folder_id')
        if folder_id:
            queryset = queryset.filter(folder_id=folder_id)
        
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        is_starred = self.request.query_params.get('is_starred')
        if is_starred is not None:
            queryset = queryset.filter(is_starred=is_starred.lower() == 'true')
        
        is_important = self.request.query_params.get('is_important')
        if is_important is not None:
            queryset = queryset.filter(is_important=is_important.lower() == 'true')
        
        has_attachments = self.request.query_params.get('has_attachments')
        if has_attachments is not None:
            if has_attachments.lower() == 'true':
                queryset = queryset.filter(attachment_count__gt=0)
            else:
                queryset = queryset.filter(attachment_count=0)
        
        from_email = self.request.query_params.get('from_email')
        if from_email:
            queryset = queryset.filter(from_email__icontains=from_email)
        
        customer_id = self.request.query_params.get('customer_id')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        
        policy_id = self.request.query_params.get('policy_id')
        if policy_id:
            queryset = queryset.filter(policy_id=policy_id)
        
        return queryset.order_by('-received_at')
    
    def retrieve(self, request, pk=None):
        """Get single email message and mark as read"""
        message = get_object_or_404(self.get_queryset(), pk=pk)
        
        # Mark as read if not already read
        if message.status == 'unread':
            message.mark_as_read()
        
        serializer = self.get_serializer(message)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark email as read"""
        message = get_object_or_404(self.get_queryset(), pk=pk)
        message.mark_as_read()
        return Response({'status': 'marked as read'})
    
    @action(detail=True, methods=['post'])
    def mark_unread(self, request, pk=None):
        """Mark email as unread"""
        message = get_object_or_404(self.get_queryset(), pk=pk)
        message.status = 'unread'
        message.save(update_fields=['status'])
        return Response({'status': 'marked as unread'})
    
    @action(detail=True, methods=['post'])
    def star(self, request, pk=None):
        """Star/unstar email"""
        message = get_object_or_404(self.get_queryset(), pk=pk)
        message.is_starred = not message.is_starred
        message.save(update_fields=['is_starred'])
        return Response({'status': 'starred' if message.is_starred else 'unstarred'})
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive email"""
        message = get_object_or_404(self.get_queryset(), pk=pk)
        message.archive()
        return Response({'status': 'archived'})
    
    @action(detail=True, methods=['post'])
    def move_to_folder(self, request, pk=None):
        """Move email to different folder"""
        message = get_object_or_404(self.get_queryset(), pk=pk)
        folder_id = request.data.get('folder_id')
        
        if not folder_id:
            return Response(
                {'error': 'folder_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            folder = EmailFolder.objects.get(id=folder_id)
            message.move_to_folder(folder)
            return Response({'status': 'moved to folder', 'folder': folder.name})
        except EmailFolder.DoesNotExist:
            return Response(
                {'error': 'Folder not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def add_tag(self, request, pk=None):
        """Add tag to email"""
        message = get_object_or_404(self.get_queryset(), pk=pk)
        tag = request.data.get('tag')
        
        if not tag:
            return Response(
                {'error': 'tag is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        message.add_tag(tag)
        return Response({'status': 'tag added', 'tag': tag})
    
    @action(detail=True, methods=['post'])
    def remove_tag(self, request, pk=None):
        """Remove tag from email"""
        message = get_object_or_404(self.get_queryset(), pk=pk)
        tag = request.data.get('tag')
        
        if not tag:
            return Response(
                {'error': 'tag is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        message.remove_tag(tag)
        return Response({'status': 'tag removed', 'tag': tag})
    
    @action(detail=True, methods=['post'])
    def reply(self, request, pk=None):
        """Reply to email"""
        message = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = EmailReplySerializer(data=request.data)
        
        if serializer.is_valid():
            success, response_message, result = email_inbox_service.reply_to_email(
                original_message_id=message.id,
                subject=serializer.validated_data['subject'],
                html_content=serializer.validated_data['html_content'],
                text_content=serializer.validated_data.get('text_content', ''),
                cc_emails=serializer.validated_data.get('cc_emails', []),
                bcc_emails=serializer.validated_data.get('bcc_emails', []),
                user=request.user
            )
            
            if success:
                return Response({
                    'status': 'reply sent',
                    'message': response_message,
                    'result': result
                })
            else:
                return Response(
                    {'error': response_message}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def forward(self, request, pk=None):
        """Forward email"""
        message = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = EmailForwardSerializer(data=request.data)
        
        if serializer.is_valid():
            success, response_message, result = email_inbox_service.forward_email(
                original_message_id=message.id,
                to_emails=serializer.validated_data['to_emails'],
                cc_emails=serializer.validated_data.get('cc_emails', []),
                bcc_emails=serializer.validated_data.get('bcc_emails', []),
                subject=serializer.validated_data.get('subject', ''),
                message=serializer.validated_data.get('message', ''),
                user=request.user
            )
            
            if success:
                return Response({
                    'status': 'email forwarded',
                    'message': response_message,
                    'result': result
                })
            else:
                return Response(
                    {'error': response_message}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """Perform bulk actions on multiple emails"""
        serializer = EmailBulkActionSerializer(data=request.data)
        
        if serializer.is_valid():
            message_ids = serializer.validated_data['message_ids']
            action = serializer.validated_data['action']
            
            messages = EmailInboxMessage.objects.filter(
                id__in=message_ids, 
                is_deleted=False
            )
            
            if not messages.exists():
                return Response(
                    {'error': 'No valid messages found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            results = []
            
            for message in messages:
                try:
                    if action == 'mark_read':
                        message.mark_as_read()
                    elif action == 'mark_unread':
                        message.status = 'unread'
                        message.save(update_fields=['status'])
                    elif action == 'star':
                        message.is_starred = True
                        message.save(update_fields=['is_starred'])
                    elif action == 'unstar':
                        message.is_starred = False
                        message.save(update_fields=['is_starred'])
                    elif action == 'archive':
                        message.archive()
                    elif action == 'delete':
                        message.is_deleted = True
                        message.save(update_fields=['is_deleted'])
                    elif action == 'move_to_folder':
                        folder_id = serializer.validated_data.get('folder_id')
                        if folder_id:
                            try:
                                folder = EmailFolder.objects.get(id=folder_id)
                                message.move_to_folder(folder)
                            except EmailFolder.DoesNotExist:
                                continue
                    elif action == 'add_tag':
                        tag = serializer.validated_data.get('tag')
                        if tag:
                            message.add_tag(tag)
                    elif action == 'remove_tag':
                        tag = serializer.validated_data.get('tag')
                        if tag:
                            message.remove_tag(tag)
                    elif action == 'mark_important':
                        message.is_important = True
                        message.save(update_fields=['is_important'])
                    elif action == 'mark_spam':
                        message.is_spam = True
                        message.save(update_fields=['is_spam'])
                    
                    results.append({'message_id': message.id, 'status': 'success'})
                    
                except Exception as e:
                    results.append({
                        'message_id': message.id, 
                        'status': 'error', 
                        'error': str(e)
                    })
            
            return Response({
                'status': 'bulk action completed',
                'action': action,
                'results': results
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search emails with advanced filters"""
        serializer = EmailSearchSerializer(data=request.query_params)
        
        if serializer.is_valid():
            search_params = serializer.validated_data
            
            # Get pagination parameters
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            
            results = email_inbox_service.search_emails(
                query=search_params.get('query', ''),
                folder_id=search_params.get('folder_id'),
                status=search_params.get('status', ''),
                category=search_params.get('category', ''),
                priority=search_params.get('priority', ''),
                is_starred=search_params.get('is_starred'),
                is_important=search_params.get('is_important'),
                has_attachments=search_params.get('has_attachments'),
                from_email=search_params.get('from_email', ''),
                to_email=search_params.get('to_email', ''),
                date_from=search_params.get('date_from'),
                date_to=search_params.get('date_to'),
                customer_id=search_params.get('customer_id'),
                policy_id=search_params.get('policy_id'),
                sort_by=search_params.get('sort_by', 'received_at'),
                sort_order=search_params.get('sort_order', 'desc'),
                page=page,
                page_size=page_size
            )
            
            # Serialize results
            emails = EmailInboxMessage.objects.filter(
                id__in=[email['id'] for email in results['emails']]
            ).order_by('-received_at')
            
            email_serializer = EmailInboxMessageSerializer(emails, many=True)
            
            return Response({
                'emails': email_serializer.data,
                'total_count': results['total_count'],
                'page': results['page'],
                'page_size': results['page_size'],
                'total_pages': results['total_pages']
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get email statistics"""
        stats = email_inbox_service.get_email_statistics()
        serializer = EmailStatsSerializer(stats)
        return Response(serializer.data)


class EmailConversationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for managing email conversations"""
    
    queryset = EmailConversation.objects.all()
    serializer_class = EmailConversationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter conversations based on query parameters"""
        queryset = EmailConversation.objects.all()
        
        # Apply filters
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        is_resolved = self.request.query_params.get('is_resolved')
        if is_resolved is not None:
            queryset = queryset.filter(is_resolved=is_resolved.lower() == 'true')
        
        is_archived = self.request.query_params.get('is_archived')
        if is_archived is not None:
            queryset = queryset.filter(is_archived=is_archived.lower() == 'true')
        
        customer_id = self.request.query_params.get('customer_id')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        
        policy_id = self.request.query_params.get('policy_id')
        if policy_id:
            queryset = queryset.filter(policy_id=policy_id)
        
        return queryset.order_by('-last_activity_at')
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Get all messages in a conversation"""
        conversation = get_object_or_404(self.get_queryset(), pk=pk)
        messages = EmailInboxMessage.objects.filter(
            thread_id=conversation.thread_id,
            is_deleted=False
        ).order_by('received_at')
        
        serializer = EmailInboxMessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_resolved(self, request, pk=None):
        """Mark conversation as resolved"""
        conversation = get_object_or_404(self.get_queryset(), pk=pk)
        conversation.mark_as_resolved()
        return Response({'status': 'conversation marked as resolved'})
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive conversation"""
        conversation = get_object_or_404(self.get_queryset(), pk=pk)
        conversation.archive()
        return Response({'status': 'conversation archived'})


class EmailFilterViewSet(viewsets.ModelViewSet):
    """ViewSet for managing email filters"""
    
    queryset = EmailFilter.objects.all()
    serializer_class = EmailFilterSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter filters based on query parameters"""
        queryset = EmailFilter.objects.all()
        
        # Apply filters
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        filter_type = self.request.query_params.get('filter_type')
        if filter_type:
            queryset = queryset.filter(filter_type=filter_type)
        
        return queryset.order_by('name')
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Test filter against sample emails"""
        email_filter = get_object_or_404(self.get_queryset(), pk=pk)
        
        # Get sample emails to test against
        sample_emails = EmailInboxMessage.objects.filter(
            is_deleted=False
        )[:10]
        
        matches = []
        for email in sample_emails:
            if email_inbox_service._filter_matches(email, email_filter.filter_rules):
                matches.append({
                    'id': email.id,
                    'subject': email.subject,
                    'from_email': email.from_email,
                    'category': email.category
                })
        
        return Response({
            'filter_id': email_filter.id,
            'filter_name': email_filter.name,
            'matches': matches,
            'total_tested': len(sample_emails),
            'match_count': len(matches)
        })


class EmailSearchQueryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing saved search queries"""
    
    queryset = EmailSearchQuery.objects.all()
    serializer_class = EmailSearchQuerySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter search queries based on user and visibility"""
        queryset = EmailSearchQuery.objects.filter(
            models.Q(is_public=True) | models.Q(created_by=self.request.user)
        )
        
        # Apply filters
        is_favorite = self.request.query_params.get('is_favorite')
        if is_favorite is not None:
            queryset = queryset.filter(is_favorite=is_favorite.lower() == 'true')
        
        return queryset.order_by('-last_used_at', 'name')
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Execute saved search query"""
        search_query = get_object_or_404(self.get_queryset(), pk=pk)
        
        # Increment use count
        search_query.increment_use_count()
        
        # Execute search with saved parameters
        search_params = search_query.search_params
        
        # Get pagination parameters
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        
        results = email_inbox_service.search_emails(
            query=search_params.get('query', ''),
            folder_id=search_params.get('folder_id'),
            status=search_params.get('status', ''),
            category=search_params.get('category', ''),
            priority=search_params.get('priority', ''),
            is_starred=search_params.get('is_starred'),
            is_important=search_params.get('is_important'),
            has_attachments=search_params.get('has_attachments'),
            from_email=search_params.get('from_email', ''),
            to_email=search_params.get('to_email', ''),
            date_from=search_params.get('date_from'),
            date_to=search_params.get('date_to'),
            customer_id=search_params.get('customer_id'),
            policy_id=search_params.get('policy_id'),
            sort_by=search_params.get('sort_by', 'received_at'),
            sort_order=search_params.get('sort_order', 'desc'),
            page=page,
            page_size=page_size
        )
        
        # Serialize results
        emails = EmailInboxMessage.objects.filter(
            id__in=[email['id'] for email in results['emails']]
        ).order_by('-received_at')
        
        email_serializer = EmailInboxMessageSerializer(emails, many=True)
        
        return Response({
            'query': search_query.name,
            'emails': email_serializer.data,
            'total_count': results['total_count'],
            'page': results['page'],
            'page_size': results['page_size'],
            'total_pages': results['total_pages']
        })


class EmailAttachmentViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for managing email attachments"""
    
    queryset = EmailAttachment.objects.all()
    serializer_class = EmailAttachmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter attachments based on message"""
        queryset = EmailAttachment.objects.all()
        
        message_id = self.request.query_params.get('message_id')
        if message_id:
            queryset = queryset.filter(message_id=message_id)
        
        return queryset.order_by('filename')
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download attachment file"""
        attachment = get_object_or_404(self.get_queryset(), pk=pk)
        
        # Check if file is safe
        if not attachment.is_safe:
            return Response(
                {'error': 'File is not safe to download'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Return file URL or trigger download
        return Response({
            'filename': attachment.filename,
            'file_url': attachment.file_url,
            'content_type': attachment.content_type,
            'size_bytes': attachment.size_bytes
        })
