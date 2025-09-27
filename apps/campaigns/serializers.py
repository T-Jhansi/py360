from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from .models import Campaign, CampaignType, CampaignRecipient, CampaignScheduleInterval
from apps.templates.models import Template
from apps.files_upload.models import FileUpload
from apps.customers.models import Customer
from apps.policies.models import Policy
from apps.renewals.models import RenewalCase

class CampaignSerializer(serializers.ModelSerializer):
    simplified_status = serializers.SerializerMethodField()

    class Meta:
        model = Campaign
        fields = [
            'id', 'name', 'campaign_type', 'description', 'status', 'simplified_status',
            'target_count','upload', 'delivered_count', 'sent_count', 'opened_count', 'clicked_count', 'total_responses',
            'channels', 'target_audience', 'communication_provider', 'started_at', 'completed_at',
            'is_recurring', 'recurrence_pattern', 'subject_line',
            'template', 'use_personalization', 'personalization_fields',
            'created_by', 'assigned_to','created_at', 'updated_at','delivery_rate', 'open_rate', 'click_rate', 'response_rate',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'delivery_rate', 'open_rate', 'click_rate', 'response_rate', 'created_by']

    def get_simplified_status(self, obj):
        """Get simplified status for frontend"""
        return obj.get_simplified_status()


class CampaignCreateSerializer(serializers.Serializer):
    """Serializer for creating campaigns based on uploaded policy files"""

    # Required fields
    file_upload_id = serializers.IntegerField(help_text="ID of the uploaded policy file from file_uploads table")
    campaign_name = serializers.CharField(max_length=200, required=False, help_text="Campaign name (defaults to file name if not provided)")
    campaign_type_id = serializers.IntegerField(help_text="ID of campaign type (should be email type)")
    template_id = serializers.IntegerField(help_text="ID of template to use for the campaign")
    communication_provider_id = serializers.IntegerField(
        required=False,
        help_text="ID of email provider to use for this campaign"
    )

    # Target audience options
    TARGET_AUDIENCE_CHOICES = [
        ('pending_renewals', 'Pending Renewals'),
        ('expired_policies', 'Expired Policies'),
        ('all_customers', 'All Customers in File'),
    ]
    target_audience_id = serializers.IntegerField(
        required=False,
        help_text="ID of existing target audience (optional - not used in date-based logic)"
    )
    target_audience_type = serializers.ChoiceField(
        choices=TARGET_AUDIENCE_CHOICES,
        required=True,
        help_text="Type of target audience to filter (required for date-based logic)"
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
        allow_null=True,
        help_text="When to send the campaign (required if schedule_type is 'scheduled')"
    )

    # Optional fields
    description = serializers.CharField(max_length=500, required=False, help_text="Campaign description")
    subject_line = serializers.CharField(max_length=200, required=False, help_text="Email subject line")
    send_immediately = serializers.BooleanField(required=False, default=False, help_text="Send emails immediately after creating campaign")
    
    # Advanced Scheduling
    enable_advanced_scheduling = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Enable multi-channel communication intervals"
    )
    schedule_intervals = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list,
        help_text="List of communication intervals for advanced scheduling"
    )

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

    def validate_target_audience_id(self, value):
        """Validate that the target audience exists (optional)"""
        if value is None:
            return value
        try:
            from apps.target_audience.models import TargetAudience
            TargetAudience.objects.get(id=value)
            return value
        except TargetAudience.DoesNotExist:
            raise serializers.ValidationError("Target audience not found")

    def validate_communication_provider_id(self, value):
        """Validate that the communication provider exists and is active"""
        if value is None:
            return value
        try:
            from apps.email_provider.models import EmailProviderConfig
            provider = EmailProviderConfig.objects.get(id=value, is_deleted=False)
            if not provider.is_active:
                raise serializers.ValidationError("Communication provider must be active")
            return value
        except EmailProviderConfig.DoesNotExist:
            raise serializers.ValidationError("Communication provider not found")

    def validate(self, data):
        """Validate the entire serializer data"""
        schedule_type = data.get('schedule_type', 'immediate')
        scheduled_at = data.get('scheduled_at')
        
        # Validate scheduled campaigns
        if schedule_type == 'scheduled':
            if not scheduled_at:
                raise serializers.ValidationError({
                    'scheduled_at': 'Scheduled time is required when schedule_type is "scheduled"'
                })
            
            # Check if scheduled time is in the future
            from django.utils import timezone
            if scheduled_at <= timezone.now():
                raise serializers.ValidationError({
                    'scheduled_at': 'Scheduled time must be in the future'
                })
        
        return data

    def validate_schedule_intervals(self, value):
        """Validate schedule intervals data"""
        if not value:
            return value
        
        valid_channels = ['email', 'whatsapp', 'sms', 'phone', 'push']
        valid_units = ['minutes', 'hours', 'days', 'weeks']
        valid_conditions = ['no_response', 'no_action', 'no_engagement', 'always']
        
        for i, interval in enumerate(value):
            # Validate required fields
            if 'channel' not in interval:
                raise serializers.ValidationError(f"Interval {i+1}: 'channel' is required")
            if 'delay_value' not in interval:
                raise serializers.ValidationError(f"Interval {i+1}: 'delay_value' is required")
            if 'delay_unit' not in interval:
                raise serializers.ValidationError(f"Interval {i+1}: 'delay_unit' is required")
            
            # Validate channel
            if interval['channel'] not in valid_channels:
                raise serializers.ValidationError(f"Interval {i+1}: Invalid channel '{interval['channel']}'. Must be one of {valid_channels}")
            
            # Validate delay unit
            if interval['delay_unit'] not in valid_units:
                raise serializers.ValidationError(f"Interval {i+1}: Invalid delay_unit '{interval['delay_unit']}'. Must be one of {valid_units}")
            
            # Validate delay value
            try:
                delay_value = int(interval['delay_value'])
                if delay_value <= 0:
                    raise serializers.ValidationError(f"Interval {i+1}: delay_value must be greater than 0")
            except (ValueError, TypeError):
                raise serializers.ValidationError(f"Interval {i+1}: delay_value must be a positive integer")
            
            # Validate trigger conditions if provided
            if 'trigger_conditions' in interval:
                for condition in interval['trigger_conditions']:
                    if condition not in valid_conditions:
                        raise serializers.ValidationError(f"Interval {i+1}: Invalid trigger condition '{condition}'. Must be one of {valid_conditions}")
        
        return value

    def validate(self, data):
        """Cross-field validation"""
        if data.get('schedule_type') == 'scheduled' and not data.get('scheduled_at'):
            raise serializers.ValidationError("scheduled_at is required when schedule_type is 'scheduled'")

        if data.get('scheduled_at') and data.get('scheduled_at') <= timezone.now():
            raise serializers.ValidationError("scheduled_at must be in the future")
        
        # Validate advanced scheduling
        if data.get('enable_advanced_scheduling') and not data.get('schedule_intervals'):
            raise serializers.ValidationError("schedule_intervals is required when enable_advanced_scheduling is True")

        return data

    def create(self, validated_data):
        """Create campaign and recipients based on target audience"""
        file_upload = FileUpload.objects.get(id=validated_data['file_upload_id'])
        campaign_type = CampaignType.objects.get(id=validated_data['campaign_type_id'])
        template = Template.objects.get(id=validated_data['template_id'])

        campaign_name = validated_data.get('campaign_name', file_upload.original_filename)

        target_audience = None
        if validated_data.get('target_audience_type'):
            try:
                target_audience = self._get_or_create_target_audience(validated_data['target_audience_type'], file_upload)
            except Exception as e:
                print(f"Warning: Could not create target audience due to permissions: {e}")
                target_audience = None
        elif validated_data.get('target_audience_id'):
            from apps.target_audience.models import TargetAudience
            target_audience = TargetAudience.objects.get(id=validated_data['target_audience_id'])

        # Handle communication provider
        communication_provider = None
        if validated_data.get('communication_provider_id'):
            from apps.email_provider.models import EmailProviderConfig
            communication_provider = EmailProviderConfig.objects.get(id=validated_data['communication_provider_id'])

        # Determine campaign status based on schedule type
        schedule_type = validated_data.get('schedule_type', 'immediate')
        scheduled_at = validated_data.get('scheduled_at')
        
        if schedule_type == 'scheduled' and scheduled_at:
            campaign_status = 'scheduled'
            started_at = scheduled_at
        else:
            campaign_status = 'draft'
            started_at = timezone.now()

        # Create the campaign with proper relationships
        campaign_data = {
            'name': campaign_name,
            'campaign_type': campaign_type,
            'template': template,
            'description': validated_data.get('description', f"Campaign created from file: {file_upload.original_filename}"),
            'status': campaign_status,
            'upload': file_upload,
            'target_audience': target_audience,
            'communication_provider': communication_provider,
            'channels': ['email'],
            'schedule_type': schedule_type,
            'scheduled_at': scheduled_at,
            'started_at': started_at,
            'subject_line': validated_data.get('subject_line', template.subject),
            'enable_advanced_scheduling': validated_data.get('enable_advanced_scheduling', False),
            'advanced_scheduling_config': validated_data.get('schedule_intervals', []),
            'created_by': self.context['request'].user,
            'assigned_to': self._get_assigned_agent()
        }

        campaign = Campaign.objects.create(**campaign_data)

        # Create advanced scheduling intervals if enabled
        if validated_data.get('enable_advanced_scheduling') and validated_data.get('schedule_intervals'):
            self._create_schedule_intervals(campaign, validated_data['schedule_intervals'])

        # Determine target audience type for recipient creation
        target_audience_type_for_recipients = validated_data.get('target_audience_type', 'all_customers')
        if validated_data.get('target_audience_id') and target_audience:
            target_audience_type_for_recipients = 'all_customers'

        target_count = self._create_campaign_recipients(campaign, target_audience_type_for_recipients, file_upload)

        campaign.target_count = target_count
        campaign.save()

        # Handle email sending based on schedule type
        if schedule_type == 'immediate' and validated_data.get('send_immediately', False):
            # Send emails immediately
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
            
        elif schedule_type == 'scheduled' and scheduled_at:
            # Schedule campaign for later - Celery will handle the sending
            try:
                from .tasks import send_scheduled_campaign_email
                import logging
                
                logger = logging.getLogger(__name__)
                logger.info(f"Scheduling campaign {campaign.pk} for {scheduled_at}")
                
                # Schedule the email sending task
                send_scheduled_campaign_email.apply_async(
                    args=[campaign.pk],
                    eta=scheduled_at
                )
                
                campaign.description += f" [Scheduled for {scheduled_at}]"
                logger.info(f"Campaign {campaign.pk} scheduled successfully for {scheduled_at}")
                
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Exception scheduling campaign: {str(e)}")
                campaign.status = 'draft'
                campaign.description += f" [Scheduling Error: {str(e)}]"
                campaign.save()

        return campaign

    def _get_or_create_target_audience(self, target_audience_type, file_upload):
        """Get or create target audience based on type"""
        from apps.target_audience.models import TargetAudience

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
                # Date-based pending renewals: policies where renewal date has arrived but not yet expired
                from datetime import date
                today = date.today()
                
                policies = Policy.objects.filter(
                    status='active',                   
                    renewal_date__lte=today,           
                    end_date__gt=today,              
                    customer__email__isnull=False,   
                    customer__email__gt=''
                ).select_related('customer')

                if file_upload:
                    upload_time = file_upload.created_at
                    time_window_start = upload_time - timedelta(hours=1)
                    time_window_end = upload_time + timedelta(hours=1)

                    file_related_policies = policies.filter(
                        created_at__range=(time_window_start, time_window_end)
                    )

                    # If we found policies in the time window, use them
                    if file_related_policies.exists():
                        policies = file_related_policies
                    else:
                        policies = policies.order_by('-created_at')[:file_upload.successful_records]

                logger.info(f"Found {policies.count()} policies with pending renewals for campaign {campaign.id if campaign else 'test'}")

                # Prepare bulk recipients
                for policy in policies:
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

            elif target_audience_type == 'expired_policies':
                # Date-based expired policies: policies where end date has passed
                from datetime import date
                today = date.today()
                
                expired_policies = Policy.objects.filter(
                    status='active',                   
                    end_date__lt=today,               
                    customer__email__isnull=False,    
                    customer__email__gt=''
                ).select_related('customer')

                # If we have a file upload, try to match policies from that upload
                if file_upload:
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

                logger.info(f"Found {expired_policies.count()} expired policies for campaign {campaign.id if campaign else 'test'}")

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
                    # For file uploads, use the successful_records count as target
                    target_count = file_upload.successful_records if file_upload.successful_records > 0 else customers.count()
                    
                    # Try to find customers created around the file upload time first
                    upload_time = file_upload.created_at
                    time_window_start = upload_time - timedelta(hours=2)
                    time_window_end = upload_time + timedelta(hours=2)

                    file_related_customers = customers.filter(
                        created_at__range=(time_window_start, time_window_end)
                    )

                    # If we found customers in the time window, use them (up to target count)
                    if file_related_customers.exists():
                        customers = file_related_customers.order_by('-created_at')[:target_count]
                        logger.info(f"Found {customers.count()} customers from file upload time window")
                    else:
                        # Fallback: use most recent customers up to target count
                        customers = customers.order_by('-created_at')[:target_count]
                        logger.info(f"Using {customers.count()} most recent customers (target: {target_count})")
                else:
                    # No file upload, get all customers
                    logger.info(f"No file upload specified, using all customers")

                logger.info(f"Total customers selected for campaign {campaign.id if campaign else 'test'}: {customers.count()}")
                
                # Debug: Log customer details
                for customer in customers[:3]:  # Log first 3 customers for debugging
                    logger.info(f"Selected customer: {customer.email} (ID: {customer.pk}, Created: {customer.created_at})")

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
                logger.info(f"Creating {len(recipients_to_create)} campaign recipients for campaign {campaign.id if campaign else 'test'}")
                recipients_created = 0
                try:
                    recipients_to_create.sort(
                        key=lambda r: (
                            getattr(r.customer, 'id', 0) or 0,
                            (getattr(getattr(r, 'policy', None), 'id', 0) or 0)
                        )
                    )
                except Exception:
                    pass

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

        logger.info(f"Successfully created {recipients_created} recipients for campaign {campaign.id if campaign else 'test'}")
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

    def _create_schedule_intervals(self, campaign, schedule_intervals):
        """Create CampaignScheduleInterval objects for advanced scheduling intervals"""
        from .models import CampaignScheduleInterval
        from apps.templates.models import Template
        from apps.email_provider.models import EmailProviderConfig
        from django.utils import timezone
        
        created_intervals = []
        
        for i, interval_data in enumerate(schedule_intervals, 1):
            # Get template if provided
            template = None
            if interval_data.get('template_id'):
                try:
                    template = Template.objects.get(id=interval_data['template_id'])
                except Template.DoesNotExist:
                    pass  
            
            provider = None
            if interval_data.get('communication_provider_id'):
                try:
                    provider = EmailProviderConfig.objects.get(
                        id=interval_data['communication_provider_id'],
                        is_deleted=False,
                        is_active=True
                    )
                except EmailProviderConfig.DoesNotExist:
                    pass  
            
            base_time = campaign.scheduled_at or campaign.started_at or timezone.now()
            scheduled_time = self._calculate_interval_time(
                base_time, 
                interval_data['delay_value'], 
                interval_data['delay_unit']
            )
            
            # Create the schedule interval
            schedule_interval = CampaignScheduleInterval.objects.create(
                campaign=campaign,
                template=template,
                communication_provider=provider,
                sequence_order=i,
                channel=interval_data['channel'],
                delay_value=interval_data['delay_value'],
                delay_unit=interval_data['delay_unit'],
                trigger_conditions=interval_data.get('trigger_conditions', ['always']),
                is_active=interval_data.get('is_active', True),
                scheduled_at=scheduled_time,
                created_by=self.context['request'].user
            )
            
            created_intervals.append(schedule_interval)
        
        return created_intervals
    
    def _calculate_interval_time(self, base_time, delay_value, delay_unit):
        """Calculate the scheduled time for an interval"""
        if delay_unit == 'minutes':
            return base_time + timedelta(minutes=delay_value)
        elif delay_unit == 'hours':
            return base_time + timedelta(hours=delay_value)
        elif delay_unit == 'days':
            return base_time + timedelta(days=delay_value)
        elif delay_unit == 'weeks':
            return base_time + timedelta(weeks=delay_value)
        else:
            return base_time

 
class CampaignScheduleIntervalSerializer(serializers.ModelSerializer):
    """Serializer for CampaignScheduleInterval model"""
    
    campaign_name = serializers.CharField(source='campaign.name', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True)
    provider_name = serializers.CharField(source='communication_provider.name', read_only=True)
    channel_display = serializers.CharField(source='get_channel_display', read_only=True)
    delay_description = serializers.CharField(source='get_delay_description', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    class Meta:
        model = CampaignScheduleInterval
        fields = [
            'id', 'campaign', 'campaign_name', 'template', 'template_name',
            'communication_provider', 'provider_name', 'sequence_order',
            'channel', 'channel_display', 'delay_value', 'delay_unit',
            'delay_description', 'trigger_conditions', 'is_active', 'is_sent',
            'scheduled_at', 'sent_at', 'created_by', 'created_by_name', 
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'campaign_name', 'template_name', 'provider_name',
            'channel_display', 'delay_description', 'created_by_name',
            'is_sent', 'sent_at', 'created_at', 'updated_at'
        ]


class CampaignScheduleIntervalCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating CampaignScheduleInterval"""
    class Meta:
        model = CampaignScheduleInterval
        fields = [
            'campaign', 'template', 'communication_provider', 'sequence_order',
            'channel', 'delay_value', 'delay_unit', 'trigger_conditions',
            'is_active', 'scheduled_at'
        ]
    
    def validate_campaign(self, value):
        """Validate that the campaign exists and is not deleted"""
        if value.is_deleted:
            raise serializers.ValidationError("Cannot create interval for deleted campaign")
        return value
    
    def validate_template(self, value):
        """Validate that the template exists and is active"""
        if value and not value.is_active:
            raise serializers.ValidationError("Cannot use inactive template")
        return value
    
    def validate_communication_provider(self, value):
        """Validate that the communication provider exists and is active"""
        if value and (value.is_deleted or not value.is_active):
            raise serializers.ValidationError("Communication provider must be active and not deleted")
        return value
    
    def validate_sequence_order(self, value):
        """Validate sequence order is unique for the campaign"""
        campaign = self.initial_data.get('campaign')
        if campaign and value:
            existing = CampaignScheduleInterval.objects.filter(
                campaign=campaign,
                sequence_order=value,
                is_deleted=False
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if existing.exists():
                raise serializers.ValidationError(
                    f"Sequence order {value} already exists for this campaign"
                )
        return value
    
    def validate_trigger_conditions(self, value):
        """Validate trigger conditions"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Trigger conditions must be a list")
        
        valid_conditions = [choice[0] for choice in CampaignScheduleInterval.TRIGGER_CONDITION_CHOICES]
        for condition in value:
            if condition not in valid_conditions:
                raise serializers.ValidationError(
                    f"Invalid trigger condition: {condition}. Must be one of {valid_conditions}"
                )
        return value
    
    def create(self, validated_data):
        """Create schedule interval with proper relationships"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class CampaignScheduleIntervalUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating CampaignScheduleInterval"""
    class Meta:
        model = CampaignScheduleInterval
        fields = [
            'template', 'communication_provider', 'sequence_order',
            'channel', 'delay_value', 'delay_unit', 'trigger_conditions',
            'is_active', 'scheduled_at'
        ]
    
    def validate_template(self, value):
        """Validate that the template exists and is active"""
        if value and not value.is_active:
            raise serializers.ValidationError("Cannot use inactive template")
        return value
    
    def validate_communication_provider(self, value):
        """Validate that the communication provider exists and is active"""
        if value and (value.is_deleted or not value.is_active):
            raise serializers.ValidationError("Communication provider must be active and not deleted")
        return value
    
    def validate_sequence_order(self, value):
        """Validate sequence order is unique for the campaign"""
        if self.instance and value:
            existing = CampaignScheduleInterval.objects.filter(
                campaign=self.instance.campaign,
                sequence_order=value,
                is_deleted=False
            ).exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise serializers.ValidationError(
                    f"Sequence order {value} already exists for this campaign"
                )
        return value
    
    def validate_trigger_conditions(self, value):
        """Validate trigger conditions"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Trigger conditions must be a list")
        
        valid_conditions = [choice[0] for choice in CampaignScheduleInterval.TRIGGER_CONDITION_CHOICES]
        for condition in value:
            if condition not in valid_conditions:
                raise serializers.ValidationError(
                    f"Invalid trigger condition: {condition}. Must be one of {valid_conditions}"
                )
        return value
    
    def update(self, instance, validated_data):
        """Update schedule interval with proper relationships"""
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)
