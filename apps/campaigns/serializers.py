from rest_framework import serializers
from django.utils import timezone
from .models import Campaign, CampaignType, CampaignRecipient
from apps.templates.models import Template
from apps.files_upload.models import FileUpload
from apps.customers.models import Customer
from apps.policies.models import Policy
from apps.renewals.models import RenewalCase

class CampaignSerializer(serializers.ModelSerializer):

    class Meta:
        model = Campaign
        fields = [
            'id', 'name', 'campaign_type', 'description', 'status',
            'target_count','upload', 'delivered_count', 'sent_count', 'opened_count', 'clicked_count', 'total_responses',
            'channels', 'target_audience', 'started_at', 'completed_at',
            'is_recurring', 'recurrence_pattern', 'subject_line',
            'template', 'use_personalization', 'personalization_fields',
            'created_by', 'assigned_to','created_at', 'updated_at','delivery_rate', 'open_rate', 'click_rate', 'response_rate',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'delivery_rate', 'open_rate', 'click_rate', 'response_rate', 'created_by']


class CampaignCreateSerializer(serializers.Serializer):
    """Serializer for creating campaigns based on uploaded policy files"""

    # Required fields
    file_upload_id = serializers.IntegerField(help_text="ID of the uploaded policy file from file_uploads table")
    campaign_name = serializers.CharField(max_length=200, required=False, help_text="Campaign name (defaults to file name if not provided)")
    campaign_type_id = serializers.IntegerField(help_text="ID of campaign type (should be email type)")
    template_id = serializers.IntegerField(help_text="ID of template to use for the campaign")

    # Target audience options
    TARGET_AUDIENCE_CHOICES = [
        ('pending_renewals', 'Pending Renewals'),
        ('expired_policies', 'Expired Policies'),
        ('all_customers', 'All Customers in File'),
    ]
    target_audience_type = serializers.ChoiceField(
        choices=TARGET_AUDIENCE_CHOICES,
        help_text="Type of target audience to filter"
    )

    # Scheduling options
    SCHEDULE_CHOICES = [
        ('immediate', 'Send Immediately'),
        ('scheduled', 'Schedule for Later'),
    ]
    schedule_type = serializers.ChoiceField(
        choices=SCHEDULE_CHOICES,
        default='immediate',
        help_text="When to send the campaign"
    )
    scheduled_at = serializers.DateTimeField(
        required=False,
        help_text="When to send the campaign (required if schedule_type is 'scheduled')"
    )

    # Optional fields
    description = serializers.CharField(max_length=500, required=False, help_text="Campaign description")
    subject_line = serializers.CharField(max_length=200, required=False, help_text="Email subject line")
    send_immediately = serializers.BooleanField(required=False, help_text="Send emails immediately after creating campaign")

    def validate_file_upload_id(self, value):
        """Validate that the file upload exists and is completed"""
        try:
            file_upload = FileUpload.objects.get(id=value)
            if file_upload.upload_status != 'completed':
                raise serializers.ValidationError("File upload must be completed before creating campaign")
            return value
        except FileUpload.DoesNotExist:
            raise serializers.ValidationError("File upload not found")

    def validate_campaign_type_id(self, value):
        """Validate that campaign type exists and is email type"""
        try:
            campaign_type = CampaignType.objects.get(id=value)
            if 'email' not in campaign_type.default_channels:
                raise serializers.ValidationError("Campaign type must support email channel")
            return value
        except CampaignType.DoesNotExist:
            raise serializers.ValidationError("Campaign type not found")

    def validate_template_id(self, value):
        """Validate that template exists and is email template"""
        try:
            template = Template.objects.get(id=value)
            print(f"Template found: ID={template.id}, Name={template.name}, Channel={template.channel}, Active={template.is_active}")
            if template.channel is not None and template.channel != 'email':
                raise serializers.ValidationError(f"Template must be an email template. Found channel: {template.channel}")
            if not template.is_active:
                raise serializers.ValidationError("Template must be active")
            return value
        except Template.DoesNotExist:
            raise serializers.ValidationError("Template not found")

    def validate(self, data):
        """Cross-field validation"""
        if data.get('schedule_type') == 'scheduled' and not data.get('scheduled_at'):
            raise serializers.ValidationError("scheduled_at is required when schedule_type is 'scheduled'")

        if data.get('scheduled_at') and data.get('scheduled_at') <= timezone.now():
            raise serializers.ValidationError("scheduled_at must be in the future")

        return data

    def create(self, validated_data):
        """Create campaign and recipients based on target audience"""
        file_upload = FileUpload.objects.get(id=validated_data['file_upload_id'])
        campaign_type = CampaignType.objects.get(id=validated_data['campaign_type_id'])
        template = Template.objects.get(id=validated_data['template_id'])

        campaign_name = validated_data.get('campaign_name', file_upload.original_filename)

        try:
            target_audience = self._get_or_create_target_audience(validated_data['target_audience_type'], file_upload)
        except Exception as e:
            print(f"Warning: Could not create target audience due to permissions: {e}")
            target_audience = None

        # Create the campaign with proper relationships
        campaign_data = {
            'name': campaign_name,
            'campaign_type': campaign_type,
            'template': template,
            'description': validated_data.get('description', f"Campaign created from file: {file_upload.original_filename}"),
            'status': 'draft',
            'upload': file_upload, 
            'channels': ['email'],
            'schedule_type': validated_data.get('schedule_type', 'immediate'),
            'scheduled_at': validated_data.get('scheduled_at'),
            'started_at': validated_data.get('scheduled_at', timezone.now()),
            'subject_line': validated_data.get('subject_line', template.subject),
            'created_by': self.context['request'].user,
            'assigned_to': self._get_assigned_agent() 
        }

        if target_audience:
            campaign_data['target_audience'] = target_audience

        campaign = Campaign.objects.create(**campaign_data)

        target_count = self._create_campaign_recipients(campaign, validated_data['target_audience_type'], file_upload)

        campaign.target_count = target_count
        campaign.save()

        if validated_data.get('send_immediately', False):
            try:
                from .services import EmailCampaignService
                import logging

                logger = logging.getLogger(__name__)
                logger.info(f"Starting immediate email sending for campaign {campaign.pk}")

                result = EmailCampaignService.send_campaign_emails(campaign.pk)

                if "error" in result:
                    logger.error(f"Email sending failed: {result['error']}")
                    campaign.status = 'draft'  
                    campaign.description += f" [Email Error: {result['error']}]"
                elif "message" in result and "No pending recipients found" in str(result.get("message", "")):
                    logger.warning(f"No recipients found: {result['message']}")
                    campaign.status = 'draft'
                    campaign.description += f" [Warning: {result['message']}]"
                elif "success" in result:
                    sent_count = int(result.get('sent_count', 0))
                    failed_count = int(result.get('failed_count', 0))

                    logger.info(f"Email sending completed: {sent_count} sent, {failed_count} failed")

                    if sent_count > 0:
                        campaign.status = 'completed'
                        campaign.description += f" [Success: {sent_count} emails sent]"
                    else:
                        campaign.status = 'draft'
                        campaign.description += f" [Warning: No emails sent, {failed_count} failed]"
                else:
                    logger.info(f"Email sending result: {result}")
                    campaign.status = 'completed'

            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Exception during email sending: {str(e)}")
                campaign.status = 'draft'  
                campaign.description += f" [Exception: {str(e)}]"

            campaign.save()

        return campaign

    def _get_or_create_target_audience(self, target_audience_type, file_upload):
        """Get or create target audience based on type"""
        from apps.TargetAudience.models import TargetAudience

        audience_name_map = {
            'pending_renewals': f"Pending Renewals - {file_upload.original_filename}",
            'expired_policies': f"Expired Policies - {file_upload.original_filename}",
            'all_customers': f"All Customers - {file_upload.original_filename}"
        }

        audience_name = audience_name_map.get(target_audience_type, f"Custom Audience - {file_upload.original_filename}")

        # Create unique key to avoid conflicts
        unique_key = f"{target_audience_type}_{file_upload.id}_{file_upload.created_at.strftime('%Y%m%d')}"

        # Try to get existing target audience first
        try:
            target_audience = TargetAudience.objects.get(key=unique_key)
            return target_audience
        except TargetAudience.DoesNotExist:
            pass

        # Create new target audience
        try:
            target_audience = TargetAudience.objects.create(
                key=unique_key,
                name=audience_name,
                description=f"Auto-created audience for {target_audience_type} from file {file_upload.original_filename}"
            )
            return target_audience
        except Exception as e:
            # If creation fails, try to get by name as fallback
            target_audience, created = TargetAudience.objects.get_or_create(
                name=audience_name,
                defaults={
                    'key': f"fallback_{target_audience_type}_{file_upload.id}",
                    'description': f"Fallback audience for {target_audience_type} from file {file_upload.original_filename}"
                }
            )
            return target_audience

    def _get_assigned_agent(self):
        """Auto-assign agent based on workload or round-robin"""
        from django.contrib.auth import get_user_model
        from django.db.models import Count

        User = get_user_model()

        available_agents = User.objects.filter(
            is_staff=True,
            is_active=True
        ).annotate(
            campaign_count=Count('assigned_campaigns')
        ).order_by('campaign_count')

        return available_agents.first() if available_agents.exists() else None

    def _create_campaign_recipients(self, campaign, target_audience_type, file_upload):
        """Create campaign recipients based on target audience type - OPTIMIZED VERSION"""
        from django.db import transaction
        import logging

        logger = logging.getLogger(__name__)
        recipients_created = 0

        # Check if recipients already exist for this campaign
        existing_recipients = CampaignRecipient.objects.filter(campaign=campaign).count()
        if existing_recipients > 0:
            logger.warning(f"Campaign {campaign.id} already has {existing_recipients} recipients. Skipping recipient creation.")
            return existing_recipients

        # Use atomic transaction for better performance
        with transaction.atomic():
            recipients_to_create = []

            if target_audience_type == 'pending_renewals':
                renewal_cases = RenewalCase.objects.filter(
                    status='pending',
                    customer__email__isnull=False,
                    customer__email__gt=''
                ).select_related('customer', 'policy')

                if file_upload:
                    from datetime import timedelta
                    upload_time = file_upload.created_at
                    time_window_start = upload_time - timedelta(hours=1)
                    time_window_end = upload_time + timedelta(hours=1)

                    file_related_cases = renewal_cases.filter(
                        created_at__range=(time_window_start, time_window_end)
                    )

                    # If we found cases in the time window, use them
                    if file_related_cases.exists():
                        renewal_cases = file_related_cases
                    else:
                        renewal_cases = renewal_cases.order_by('-created_at')[:file_upload.successful_records]

                logger.info(f"Found {renewal_cases.count()} pending renewal cases for campaign {campaign.id}")

                # Prepare bulk recipients
                for renewal_case in renewal_cases:
                    recipients_to_create.append(
                        CampaignRecipient(
                            campaign=campaign,
                            customer=renewal_case.customer,
                            policy=renewal_case.policy,
                            email_status='pending',
                            whatsapp_status='pending',
                            sms_status='pending'
                        )
                    )

            elif target_audience_type == 'expired_policies':
                # Get customers with expired policies - IMPROVED LOGIC
                expired_policies = Policy.objects.filter(
                    status='expired',
                    customer__email__isnull=False,
                    customer__email__gt=''
                ).select_related('customer')

                # If we have a file upload, try to match policies from that upload
                if file_upload:
                    from datetime import timedelta
                    upload_time = file_upload.created_at
                    time_window_start = upload_time - timedelta(hours=1)
                    time_window_end = upload_time + timedelta(hours=1)

                    file_related_policies = expired_policies.filter(
                        created_at__range=(time_window_start, time_window_end)
                    )

                    # If we found policies in the time window, use them
                    if file_related_policies.exists():
                        expired_policies = file_related_policies
                    else:
                        expired_policies = expired_policies.order_by('-created_at')[:file_upload.successful_records]

                logger.info(f"Found {expired_policies.count()} expired policies for campaign {campaign.id}")

                # Prepare bulk recipients
                for policy in expired_policies:
                    recipients_to_create.append(
                        CampaignRecipient(
                            campaign=campaign,
                            customer=policy.customer,
                            policy=policy,
                            email_status='pending',
                            whatsapp_status='pending',
                            sms_status='pending'
                        )
                    )

            elif target_audience_type == 'all_customers':
                # Get customers from file upload - IMPROVED LOGIC
                customers = Customer.objects.filter(
                    is_deleted=False,
                    email__isnull=False,
                    email__gt=''
                )

                if file_upload:
                    from datetime import timedelta
                    upload_time = file_upload.created_at
                    time_window_start = upload_time - timedelta(hours=1)
                    time_window_end = upload_time + timedelta(hours=2)

                    file_related_customers = customers.filter(
                        created_at__range=(time_window_start, time_window_end)
                    )

                    # If we found customers in the time window, use them
                    if file_related_customers.exists():
                        customers = file_related_customers
                        logger.info(f"Found {customers.count()} customers from file upload time window")
                    else:
                        target_count = file_upload.successful_records if file_upload.successful_records > 0 else 10
                        customers = customers.order_by('-created_at')[:target_count]
                        logger.info(f"Using {customers.count()} most recent customers (target: {target_count})")
                else:
                    # No file upload, get all customers
                    logger.info(f"No file upload specified, using all customers")

                logger.info(f"Total customers selected for campaign {campaign.id}: {customers.count()}")

                customer_ids = list(customers.values_list('id', flat=True))

                latest_policies = {}
                if customer_ids:
                    all_policies = Policy.objects.filter(
                        customer__in=customer_ids
                    ).select_related('customer').order_by('customer', '-created_at')

                    seen_customers = set()
                    for policy in all_policies:
                        if policy.customer.pk not in seen_customers:
                            latest_policies[policy.customer.pk] = policy
                            seen_customers.add(policy.customer.pk)

                for customer in customers:
                    latest_policy = latest_policies.get(customer.pk)

                    recipients_to_create.append(
                        CampaignRecipient(
                            campaign=campaign,
                            customer=customer,
                            policy=latest_policy,
                            email_status='pending',
                            whatsapp_status='pending',
                            sms_status='pending'
                        )
                    )

            if recipients_to_create:
                recipients_created = 0

                existing_customer_ids = set(
                    CampaignRecipient.objects.filter(campaign=campaign).values_list('customer_id', flat=True)
                )

                for recipient_data in recipients_to_create:
                    if recipient_data.customer.id in existing_customer_ids:
                        continue

                    try:
                        import uuid
                        import hashlib
                        unique_string = f"{campaign.id}-{recipient_data.customer.id}-{uuid.uuid4()}"
                        tracking_id = hashlib.sha256(unique_string.encode()).hexdigest()[:32]

                        recipient = CampaignRecipient.objects.create(
                            campaign=recipient_data.campaign,
                            customer=recipient_data.customer,
                            policy=recipient_data.policy,
                            email_status=recipient_data.email_status,
                            whatsapp_status=recipient_data.whatsapp_status,
                            sms_status=recipient_data.sms_status,
                            tracking_id=tracking_id,
                            created_by=self.context['request'].user
                        )
                        recipients_created += 1
                        logger.debug(f"Created recipient for customer {recipient_data.customer.email}")

                        self._add_email_tracking(recipient)

                    except Exception as e:
                        logger.warning(f"Failed to create recipient for customer {recipient_data.customer.id}: {str(e)}")
                        continue

        logger.info(f"Successfully created {recipients_created} recipients for campaign {campaign.id}")
        return recipients_created

    def _add_email_tracking(self, recipient):
        """Add tracking pixel and convert links for email tracking"""
        import logging
        logger = logging.getLogger(__name__)

        try:
            from django.conf import settings

            base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')

            tracking_pixel_url = f"{base_url}/api/campaigns/track-open/?t={recipient.tracking_id}"

            tracking_pixel = f'<img src="{tracking_pixel_url}" width="1" height="1" style="display:none;" alt="" />'

            logger.debug(f"Added tracking pixel for recipient {recipient.id}: {tracking_pixel_url}")

        except Exception as e:
            logger.warning(f"Failed to add email tracking for recipient {recipient.id}: {str(e)}")
