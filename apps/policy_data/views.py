import pandas as pd
import hashlib
import os
from datetime import datetime, date, timedelta
from decimal import Decimal
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db import transaction, IntegrityError
from django.db.models import Count
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from apps.customers.models import Customer
from apps.files_upload.models import FileUpload
from apps.uploads.models import FileUpload as UploadsFileUpload
from apps.policies.models import Policy, PolicyType
from .utils import generate_customer_code, generate_case_number, generate_policy_number, generate_batch_code
from .serializers import (
    FileUploadSerializer,
    EnhancedFileUploadSerializer,
    FileUploadRequestSerializer
)

User = get_user_model()

def get_next_available_agent():
    try:
        available_agents = User.objects.filter(
            status='active',
            is_active=True
        ).annotate(
            current_workload=Count('assigned_customers')
        ).order_by('current_workload', 'first_name')

        if available_agents.exists():
            return available_agents.first()
        return None
    except Exception as e:
        print(f"Error getting next available agent: {e}")
        return None

def get_customer_previous_policy_end_date(customer, current_policy_start_date=None, exclude_policy_id=None):
    from apps.policies.models import Policy

    try:
        # Handle both Customer instance and customer_id
        customer_id = customer.id if hasattr(customer, 'id') else customer

        # Build query to find previous policies
        query = Policy.objects.filter(customer_id=customer_id)

        # Exclude current policy if specified
        if exclude_policy_id:
            query = query.exclude(id=exclude_policy_id)

        # If we have current policy start date, only look for policies that ended before it
        if current_policy_start_date:
            if isinstance(current_policy_start_date, datetime):
                current_policy_start_date = current_policy_start_date.date()
            query = query.filter(end_date__lt=current_policy_start_date)

        # Get the most recent previous policy by end_date
        previous_policy = query.order_by('-end_date').first()

        if previous_policy:
            return previous_policy.end_date

        return None

    except Exception as e:
        # Log error but don't break the flow
        print(f"Error getting previous policy end date: {e}")
        return None


def calculate_policy_and_renewal_status(end_date, start_date=None, grace_period_days=30,
                                      customer=None, exclude_policy_id=None):
    today = date.today()

    if isinstance(end_date, datetime):
        end_date = end_date.date()

    if isinstance(start_date, datetime):
        start_date = start_date.date()

    days_to_expiry = (end_date - today).days
    pre_due_threshold = 60
    policy_due_threshold = 15
    overdue_threshold = today - timedelta(days=grace_period_days)

    # Enhanced renewal detection logic
    # First check: Original logic for backward compatibility
    if start_date and start_date > end_date:
        return 'active', 'renewed'

    # Second check: New logic - compare with previous policy end date
    if customer and start_date:
        previous_policy_end_date = get_customer_previous_policy_end_date(
            customer, start_date, exclude_policy_id
        )

        if previous_policy_end_date and start_date > previous_policy_end_date:
            # This is a renewal - new policy starts after previous policy ended
            return 'active', 'renewed'

    # Existing status calculation logic (unchanged)
    if end_date < today:
        if end_date >= overdue_threshold:
            policy_status = 'expired'
            renewal_status = 'pending'
        else:
            policy_status = 'expired'
            renewal_status = 'overdue'

    elif 0 <= days_to_expiry <= policy_due_threshold:
        policy_status = 'pending'
        renewal_status = 'due'

    elif policy_due_threshold < days_to_expiry <= grace_period_days:
        policy_status = 'expiring_soon'
        renewal_status = 'due'

    elif grace_period_days < days_to_expiry <= pre_due_threshold:
        policy_status = 'active'
        renewal_status = 'not_required'

    else:
        policy_status = 'active'
        renewal_status = 'not_required'

    return policy_status, renewal_status

class FileUploadViewSet(viewsets.ModelViewSet):
    """Enhanced file upload viewset with comprehensive Excel processing"""

    queryset = FileUpload.objects.all()
    serializer_class = FileUploadSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """Upload and process Excel file with enhanced validation"""
        try:
            uploaded_file = request.FILES.get('file') or request.FILES.get('upload_file')
            if not uploaded_file:
                return Response({'error': 'No file provided.'}, status=status.HTTP_400_BAD_REQUEST)
            validation_result = self._validate_file(uploaded_file)
            if not validation_result['valid']:
                return Response({
                    'error': validation_result['error'],
                    'details': validation_result.get('details', {})
                }, status=status.HTTP_400_BAD_REQUEST)

            file_hash = self._calculate_file_hash(uploaded_file)
            existing_file = UploadsFileUpload.objects.filter(file_hash=file_hash).first()

            if existing_file:
                return Response({
                    'error': 'Duplicate file detected. This file has already been uploaded.',
                    'details': {
                        'existing_file_id': existing_file.pk,
                        'existing_file_name': existing_file.original_name,
                        'uploaded_at': existing_file.created_at
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                file_upload_record, uploads_record = self._create_file_records(
                    uploaded_file, file_hash, request.user
                )
            except Exception as create_error:
                raise create_error

            try:
                processing_result = self._process_uploaded_excel_file(uploads_record, request.user, file_upload_record)
            except Exception as process_error:
                uploads_record.status = 'failed'
                uploads_record.error_message = str(process_error)
                uploads_record.updated_by = request.user
                uploads_record.save()

                if file_upload_record:
                    file_upload_record.upload_status = 'failed'
                    file_upload_record.error_details = {'error': str(process_error), 'type': 'processing_error'}
                    file_upload_record.processing_completed_at = timezone.now()
                    file_upload_record.updated_by = request.user
                    file_upload_record.save()
                raise process_error

            response_data = {
                'success': True,
                'message': 'File uploaded successfully',
                'data': {
                    'uploads_file_id': uploads_record.pk,
                    'file_name': uploaded_file.name,
                    'file_size': uploaded_file.size,
                    'file_hash': file_hash,
                    'upload_status': uploads_record.status,
                    'created_at': uploads_record.created_at.isoformat(),
                    'secure_filename': uploads_record.metadata.get('secure_filename', uploaded_file.name),
                    'category': uploads_record.category,
                    'subcategory': uploads_record.subcategory
                }
            }

            if file_upload_record and file_upload_record.processing_result:
                try:
                    import json
                    processing_details = json.loads(file_upload_record.processing_result) if isinstance(file_upload_record.processing_result, str) else file_upload_record.processing_result
                    response_data['processing_details'] = processing_details
                except (json.JSONDecodeError, TypeError):
                    response_data['processing_details'] = file_upload_record.processing_result

            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            error_type = type(e).__name__

            return Response({
                'error': f'File processing failed: {str(e)}',
                'error_type': error_type,
                'details': {
                    'step': 'Exception caught in main try-catch',
                    'user': str(request.user),
                    'files_in_request': list(request.FILES.keys())
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _validate_file(self, file):
        """Enhanced file validation with security checks"""
        allowed_extensions = ['.xlsx', '.xls', '.csv', '.txt']
        allowed_mime_types = [
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-excel',
            'text/csv',
            'text/plain'
        ]

        file_extension = os.path.splitext(file.name)[1].lower()
        if file_extension not in allowed_extensions:
            return {
                'valid': False,
                'error': 'Invalid file type. Only Excel files (.xlsx, .xls) are allowed.',
                'details': {'file_extension': file_extension, 'allowed_extensions': allowed_extensions}
            }

        max_file_size = 50 * 1024 * 1024 
        if file.size > max_file_size:
            return {
                'valid': False,
                'error': 'File too large. Maximum size is 50MB.',
                'details': {
                    'file_size': file.size,
                    'max_size': max_file_size,
                    'file_size_mb': round(file.size / (1024 * 1024), 2)
                }
            }

        if hasattr(file, 'content_type') and file.content_type not in allowed_mime_types:
            return {
                'valid': False,
                'error': 'Invalid file content type.',
                'details': {'content_type': file.content_type, 'allowed_types': allowed_mime_types}
            }

        try:
            file.seek(0)
            header = file.read(8)
            file.seek(0)

            xlsx_signature = b'\x50\x4B\x03\x04' 
            xls_signature = b'\xD0\xCF\x11\xE0'  

            if not (header.startswith(xlsx_signature) or header.startswith(xls_signature)):
                return {
                    'valid': False,
                    'error': 'File content does not match Excel format.',
                    'details': {'file_signature': header.hex()}
                }

        except Exception:
            return {
                'valid': False,
                'error': 'Unable to validate file content.'
            }

        return {'valid': True}

    def _calculate_file_hash(self, file):
        """Calculate SHA-256 hash of the file"""
        hash_sha256 = hashlib.sha256()
        for chunk in file.chunks():
            hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def _create_file_records(self, uploaded_file, file_hash, user):
        """Create records in both file upload tables with secure naming"""
        try:
            secure_filename = self._generate_secure_filename(uploaded_file.name, user.id)

            try:
                uploads_record = UploadsFileUpload.objects.create(
                    file=uploaded_file,
                    original_name=uploaded_file.name,
                    file_size=uploaded_file.size,
                    mime_type=uploaded_file.content_type,
                    file_hash=file_hash,
                    category='import',
                    subcategory='excel_data',
                    status='completed',
                    is_public=False,
                    created_by=user,
                    metadata={
                        'upload_source': 'policy_data_import',
                        'upload_timestamp': timezone.now().isoformat(),
                        'user_id': user.id,
                        'user_email': user.email,
                        'secure_filename': secure_filename,
                        'virus_scan_required': True
                    }
                )

                try:
                    file_upload_record = self._create_file_uploads_record(uploads_record, user)
                except Exception:
                    file_upload_record = None

            except Exception as e2:
                raise e2

            return file_upload_record, uploads_record

        except Exception as e:
            raise e

    def _generate_secure_filename(self, original_filename, user_id):
        """Generate secure filename with timestamp and user ID"""
        import uuid
        from datetime import datetime

        file_extension = os.path.splitext(original_filename)[1].lower()

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        secure_filename = f"policy_import_{user_id}_{timestamp}_{unique_id}{file_extension}"

        return secure_filename

    def _create_file_uploads_record(self, uploads_record, user):
        """Create record in file_uploads table with all required fields"""
        import json
        try:
            file_upload_record = FileUpload.objects.create(
                uploaded_file=uploads_record.file,
                filename=uploads_record.original_name,
                original_filename=uploads_record.original_name,
                file_size=uploads_record.file_size,
                file_type=uploads_record.mime_type,
                upload_path=uploads_record.file.path if uploads_record.file else '',
                total_records=0,  
                successful_records=0,
                failed_records=0,
                upload_status='processing',
                uploaded_by=user,
                processing_started_at=timezone.now(),
                processing_result=json.dumps({
                    'file_info': {
                        'name': uploads_record.original_name,
                        'size': uploads_record.file_size,
                        'content_type': uploads_record.mime_type,
                        'hash': uploads_record.file_hash,
                    },
                    'processing_status': 'started',
                    'timestamp': timezone.now().isoformat(),
                    'columns_processed': [],
                    'validation_errors': [],
                    'processing_errors': []
                }),
                created_by=user,
            )
            return file_upload_record
        except Exception as e:
            raise e

    def _process_uploaded_excel_file(self, uploads_record, user, file_upload_record=None):
        """Process Excel file directly from uploads_record"""
        try:
            df = pd.read_excel(uploads_record.file.path)

            validation_result = self._validate_excel_structure_flexible(df)
            if not validation_result['valid']:
                uploads_record.status = 'failed'
                uploads_record.error_message = validation_result['error']
                uploads_record.save()
                return validation_result

            processing_result = self._process_excel_data(df, user)

            uploads_record.status = 'completed' if processing_result['failed_records'] == 0 else 'partial'
            uploads_record.metadata.update({
                'processing_completed': True,
                'total_records': processing_result['total_records'],
                'successful_records': processing_result['successful_records'],
                'failed_records': processing_result['failed_records'],
                'created_customers': processing_result['created_customers'],
                'created_policies': processing_result['created_policies'],
                'created_renewal_cases': processing_result['created_renewal_cases']
            })
            uploads_record.save()

            if file_upload_record:
                file_upload_record.upload_status = 'completed' if processing_result['failed_records'] == 0 else 'partial'
                file_upload_record.total_records = processing_result['total_records']
                file_upload_record.successful_records = processing_result['successful_records']
                file_upload_record.failed_records = processing_result['failed_records']
                file_upload_record.processing_completed_at = timezone.now()
                import json
                processing_summary = {
                    'status': 'completed' if processing_result['failed_records'] == 0 else 'partial',
                    'total_records': processing_result['total_records'],
                    'successful_records': processing_result['successful_records'],
                    'failed_records': processing_result['failed_records'],
                    'created_customers': processing_result['created_customers'],
                    'created_policies': processing_result['created_policies'],
                    'created_renewal_cases': processing_result['created_renewal_cases'],
                    'errors': processing_result.get('errors', [])
                }
                file_upload_record.processing_result = json.dumps(processing_summary)
                file_upload_record.updated_by = user
                file_upload_record.save()


            return processing_result

        except Exception as e:

            uploads_record.status = 'failed'
            uploads_record.error_message = str(e)
            uploads_record.updated_by = user
            uploads_record.save()
            raise e

    def _validate_excel_structure_flexible(self, df):
        core_required = ['first_name', 'last_name', 'email']

        missing_core = [col for col in core_required if col not in df.columns]

        if missing_core:
            return {
                'valid': False,
                'error': f"Missing core required columns: {', '.join(missing_core)}"
            }

        if df.empty:
            return {
                'valid': False,
                'error': "Excel file is empty"
            }

        available_columns = list(df.columns)
        print(f"Available columns in Excel: {available_columns}")

        has_channel = 'channel' in df.columns
        has_channel_source = 'channel_source' in df.columns

        if has_channel or has_channel_source:
            print(f"Channel tracking columns found - channel: {has_channel}, channel_source: {has_channel_source}")

        return {'valid': True}

    def _process_excel_file(self, file_upload_record, uploads_record, user):
        """Process Excel file and extract data"""
        try:
            df = pd.read_excel(file_upload_record.uploaded_file.path)

            validation_result = self._validate_excel_structure(df)
            if not validation_result['valid']:
                self._mark_processing_failed(
                    file_upload_record, uploads_record, validation_result['error'], user
                )
                return validation_result

            processing_result = self._process_excel_data(df, user)

            self._update_file_records_with_results(
                file_upload_record, uploads_record, processing_result, user
            )

            return processing_result

        except Exception as e:
            error_msg = f"Excel processing error: {str(e)}"
            self._mark_processing_failed(file_upload_record, uploads_record, error_msg, user)
            return {'error': error_msg, 'valid': False}

    def _validate_excel_structure(self, df):
        required_columns = [
            'first_name', 'last_name', 'email', 'phone', 'date_of_birth',
            'gender', 'address_line1', 'kyc_status', 'kyc_documents',
            'communication_preferences', 'policy_number', 'policy_type',
            'premium_amount', 'start_date', 'end_date', 'nominee_name',
            'nominee_relationship', 'agent_name', 'agent_code',
            'priority', 'renewal_amount', 'payment_status',
            'last_contact_date', 'notes'
        ]

        has_comm_attempts = 'communication_attempts' in df.columns or 'communications_attempts' in df.columns
        if not has_comm_attempts:
            required_columns.append('communication_attempts')

        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            return {
                'valid': False,
                'error': f"Missing required columns: {', '.join(missing_columns)}"
            }

        if df.empty:
            return {
                'valid': False,
                'error': "Excel file is empty"
            }

        return {'valid': True}

    def _process_excel_data(self, df, user):
        """Process Excel data and create database records"""
        total_records = len(df)
        successful_records = 0
        failed_records = 0
        errors = []
        created_customers = 0
        created_policies = 0
        created_renewal_cases = 0

        batch_code = generate_batch_code()
        print(f"Generated batch code: {batch_code}")

        for idx, (_, row) in enumerate(df.iterrows()):
            try:
                with transaction.atomic():
                    customer, customer_created = self._process_customer_data(row, user)
                    if customer_created:
                        created_customers += 1

                    policy, policy_created = self._process_policy_data(row, customer, user)
                    if policy_created:
                        created_policies += 1

                    self._process_renewal_case_data(row, customer, policy, user, batch_code)
                    created_renewal_cases += 1

                    successful_records += 1

            except Exception as e:
                failed_records += 1
                error_msg = f"Row {idx + 1}: {str(e)}"
                errors.append(error_msg)

        return {
            'total_records': total_records,
            'successful_records': successful_records,
            'failed_records': failed_records,
            'errors': errors,
            'created_customers': created_customers,
            'created_policies': created_policies,
            'created_renewal_cases': created_renewal_cases,
            'valid': True
        }

    def _process_customer_data(self, row, user):
        """Process customer data from Excel row"""
        email = row['email']
        phone = str(row.get('phone', ''))

        customer = Customer.objects.filter(email=email).first()

        if not customer and phone:
            customer = Customer.objects.filter(phone=phone).first()

        customer_created = False

        if not customer:
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    customer_code = generate_customer_code()

                    priority = str(row.get('priority', 'medium')).lower()
                    if priority not in ['low', 'medium', 'high', 'urgent']:
                        priority = 'medium'

                    assigned_agent = get_next_available_agent()

                    customer = Customer.objects.create(
                        customer_code=customer_code,
                        first_name=row['first_name'],
                        last_name=row['last_name'],
                        email=email,
                        phone=phone,
                        date_of_birth=self._parse_date(row.get('date_of_birth')),
                        gender=row.get('gender', 'male').lower() if row.get('gender') else 'male',
                        address_line1=str(row.get('address_line1', '') or row.get('address', '')),
                        address_line2=str(row.get('address_line2', '')),
                        city=str(row.get('city', '')),
                        state=str(row.get('state', '')),
                        postal_code=str(row.get('postalcode', '') or row.get('postal_code', '')),
                        country=str(row.get('country', 'India')),
                        kyc_status=row.get('kyc_status', 'pending').lower(),
                        kyc_documents=str(row.get('kyc_documents', '')),
                        communication_preferences=str(row.get('communication_preferences', '')),
                        priority=priority,
                        assigned_agent=assigned_agent, 
                        created_by=user,
                        updated_by=user
                    )
                    customer_created = True

                    if assigned_agent:
                        print(f"✅ Auto-assigned agent {assigned_agent.get_full_name()} to customer {customer.customer_code}")
                    else:
                        print(f"⚠️  No agents available for auto-assignment to customer {customer.customer_code}")

                    break
                except IntegrityError as e:
                    if 'customer_code' in str(e) and attempt < max_retries - 1:
                        continue
                    else:
                        raise
        return customer, customer_created

    def _process_policy_data(self, row, customer, user):
        excel_policy_number = row.get('policy_number')
        if excel_policy_number and str(excel_policy_number).strip():
            policy_number = str(excel_policy_number).strip()
        else:
            policy_number = generate_policy_number()

        policy = Policy.objects.filter(policy_number=policy_number).first()
        policy_created = False

        if not policy:
            policy_type_name = str(row.get('policy_type', 'General'))
            policy_type, _ = PolicyType.objects.get_or_create(
                name=policy_type_name,
                defaults={
                    'code': policy_type_name.upper()[:10],
                    'description': f'Auto-created policy type for {policy_type_name}',
                    'created_by': user,
                    'updated_by': user
                }
            )

            payment_frequency = str(row.get('payment_frequency', 'yearly')).lower()
            if payment_frequency not in ['monthly', 'quarterly', 'half_yearly', 'yearly']:
                payment_frequency = 'yearly'

            start_date = self._parse_date(row.get('start_date'))
            end_date = self._parse_date(row.get('end_date'))

            if start_date is None:
                from datetime import date
                start_date = date.today()

            if end_date is None:
                from datetime import date, timedelta
                if payment_frequency == 'monthly':
                    end_date = start_date + timedelta(days=30)
                elif payment_frequency == 'quarterly':
                    end_date = start_date + timedelta(days=90)
                elif payment_frequency == 'half_yearly':
                    end_date = start_date + timedelta(days=180)
                else:  
                    end_date = start_date + timedelta(days=365)

            # Enhanced renewal detection: pass customer and start_date for cross-policy comparison
            policy_status, _ = calculate_policy_and_renewal_status(
                end_date,
                start_date=start_date,
                customer=customer
            )

            policy = Policy.objects.create(
                policy_number=policy_number,
                customer=customer,
                policy_type=policy_type,
                start_date=start_date,
                end_date=end_date,
                premium_amount=Decimal(str(row.get('premium_amount', 0))),
                sum_assured=Decimal(str(row.get('sum_assured', 0))),
                payment_frequency=payment_frequency,
                status=policy_status,
                nominee_name=str(row.get('nominee_name', '')),
                nominee_relationship=str(row.get('nominee_relationship', '')),
                nominee_contact=str(row.get('nominee_contact', '')),
                agent_name=str(row.get('agent_name', '')),
                agent_code=str(row.get('agent_code', '')),
                created_by=user,
                last_modified_by=user
            )
            policy_created = True

        return policy, policy_created

    def _process_renewal_case_data(self, row, customer, policy, user, batch_code):
        max_retries = 5
        case_number = None
        for attempt in range(max_retries):
            case_number = generate_case_number()
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM renewal_cases WHERE case_number = %s", [case_number])
                result = cursor.fetchone()
                if result and result[0] == 0:
                    break
            if attempt == max_retries - 1:
                raise ValueError(f"Could not generate unique case number after {max_retries} attempts")

        # Enhanced renewal detection: pass customer and policy dates for cross-policy comparison
        _, renewal_status = calculate_policy_and_renewal_status(
            policy.end_date,
            start_date=policy.start_date,
            customer=customer
        )

        renewal_priority = str(row.get('priority', 'medium')).lower()
        if renewal_priority not in ['low', 'medium', 'high', 'urgent']:
            renewal_priority = 'medium'

        payment_status = str(row.get('payment_status', 'pending')).lower()
        if payment_status not in ['pending', 'completed', 'failed', 'refunded']:
            payment_status = 'pending'

        renewal_amount = row.get('renewal_amount')
        if renewal_amount is None or pd.isna(renewal_amount):
            renewal_amount = policy.premium_amount
        else:
            renewal_amount = Decimal(str(renewal_amount))

        assigned_to_id = None
        if 'assigned_to' in row and row['assigned_to']:
            assigned_to_value = str(row['assigned_to']).strip()
            from django.contrib.auth import get_user_model
            from django.db import models
            User = get_user_model()

            if assigned_to_value.isdigit():
                try:
                    assigned_user = User.objects.get(id=int(assigned_to_value))
                    assigned_to_id = assigned_user.pk
                except User.DoesNotExist:
                    assigned_user = None

            if not assigned_to_id:
                assigned_user = User.objects.filter(
                    models.Q(email=assigned_to_value) | models.Q(employee_id=assigned_to_value)
                ).first()
                if assigned_user:
                    assigned_to_id = assigned_user.pk

        if not assigned_to_id:
            assigned_to_id = user.id

        from apps.renewals.models import RenewalCase
        from django.contrib.auth import get_user_model
        User = get_user_model()

        assigned_user = None
        if assigned_to_id:
            try:
                assigned_user = User.objects.get(id=assigned_to_id)
            except User.DoesNotExist:
                assigned_user = user  
        else:
            assigned_user = user

        channel_id = self._get_or_create_channel(row, user)

        renewal_case = RenewalCase.objects.create(
            case_number=case_number,
            batch_code=batch_code,
            customer=customer,
            policy=policy,
            status=renewal_status,
            priority=renewal_priority,
            renewal_amount=renewal_amount,
            payment_status=payment_status,
            payment_date=self._parse_datetime(row.get('payment_date')),
            communication_attempts=int(row.get('communication_attempts') or row.get('communications_attempts', 0)) if (row.get('communication_attempts') or row.get('communications_attempts')) else 0,
            last_contact_date=self._parse_datetime(row.get('last_contact_date')),
            channel_id=channel_id,
            notes=str(row.get('notes', '')),
            assigned_to=assigned_user,
            created_by=user,
            updated_by=user
        )

        return renewal_case

    def _get_or_create_channel(self, row, user):
        """Get or create channel based on Excel data"""
        from apps.channels.models import Channel

        channel_name = str(row.get('channel', 'Online')).strip()
        channel_source = str(row.get('channel_source', 'Website')).strip()

        channel_name_normalized = channel_name.lower()
        channel_source_normalized = channel_source.lower()

        combined_name = f"{channel_name} - {channel_source}"

        channel_type_mapping = {
            'online': 'online',
            'mobile': 'mobile',
            'offline': 'offline',
            'phone': 'phone',
            'agent': 'agent',
            'telecalling': 'phone',
            'call center': 'phone',
            'partner': 'agent',
            'branch': 'offline',
            'website': 'online',
            'mobile app': 'mobile'
        }

        channel_type = 'online'
        for key, value in channel_type_mapping.items():
            if key in channel_name_normalized:
                channel_type = value
                break

        existing_channel = Channel.objects.filter(
            name__iexact=combined_name
        ).first()

        if existing_channel:
            return existing_channel

        try:
            new_channel = Channel.objects.create(
                name=combined_name,
                channel_type=channel_type,
                description=f"Auto-created from Excel upload - Channel: {channel_name}, Source: {channel_source}",
                status='active',
                priority='medium',
                created_by=user,
                updated_by=user
            )
            return new_channel
        except Exception as e:
            default_channel = Channel.objects.filter(name__iexact='Online - Website').first()
            if default_channel:
                return default_channel

            default_channel = Channel.objects.create(
                name='Online - Website',
                channel_type='online',
                description='Default channel for online website traffic',
                status='active',
                priority='medium',
                created_by=user,
                updated_by=user
            )
            return default_channel

    def _parse_date(self, date_value):
        """Parse date from various formats"""
        if pd.isna(date_value) or date_value is None:
            return None

        if isinstance(date_value, (date, datetime)):
            return date_value.date() if isinstance(date_value, datetime) else date_value

        try:
            return pd.to_datetime(date_value).date()
        except:
            return None

    def _parse_datetime(self, datetime_value):
        """Parse datetime from various formats"""
        if pd.isna(datetime_value) or datetime_value is None:
            return None

        if isinstance(datetime_value, datetime):
            return datetime_value

        if isinstance(datetime_value, date):
            return datetime.combine(datetime_value, datetime.min.time())

        try:
            return pd.to_datetime(datetime_value)
        except:
            return None

    def _update_file_records_with_results(self, file_upload_record, uploads_record, result, user):
        file_upload_record.total_records = result['total_records']
        file_upload_record.successful_records = result['successful_records']
        file_upload_record.failed_records = result['failed_records']
        file_upload_record.upload_status = 'completed' if result['failed_records'] == 0 else 'partial'
        file_upload_record.processing_completed_at = timezone.now()
        file_upload_record.updated_by = user  

        import json

        result_summary = {
            'processing_summary': f"Processing completed. Total: {result['total_records']}, Success: {result['successful_records']}, Failed: {result['failed_records']}",
            'total_records': result['total_records'],
            'successful_records': result['successful_records'],
            'failed_records': result['failed_records'],
            'errors': result.get('errors', [])[:3],  
            'status': 'completed' if result['failed_records'] == 0 else 'partial',
            'created_customers': result.get('created_customers', 0),
            'created_policies': result.get('created_policies', 0),
            'created_renewal_cases': result.get('created_renewal_cases', 0)
        }

        file_upload_record.error_details = result_summary
        file_upload_record.processing_result = json.dumps(result_summary) 
        file_upload_record.save()

        uploads_record.status = 'completed' if result['failed_records'] == 0 else 'failed'
        uploads_record.error_message = result_summary['processing_summary']
        uploads_record.processing_result = json.dumps(result_summary) 
        uploads_record.updated_by = user 
        uploads_record.save(update_fields=['status', 'error_message', 'processing_result', 'updated_by'])

    def _mark_processing_failed(self, file_upload_record, uploads_record, error_msg, user):
       
        import json

        failure_result = {
            'status': 'failed',
            'error': error_msg,
            'type': 'processing_failed',
            'total_records': 0,
            'successful_records': 0,
            'failed_records': 0,
            'created_customers': 0,
            'created_policies': 0,
            'created_renewal_cases': 0
        }

        file_upload_record.upload_status = 'failed'
        file_upload_record.error_details = failure_result
        file_upload_record.processing_result = json.dumps(failure_result)
        file_upload_record.processing_completed_at = timezone.now()
        file_upload_record.updated_by = user 
        file_upload_record.save()

        uploads_record.status = 'failed'
        uploads_record.error_message = error_msg
        uploads_record.processing_result = json.dumps(failure_result)
        uploads_record.updated_by = user 
        uploads_record.save(update_fields=['status', 'error_message', 'processing_result', 'updated_by'])

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
       
        try:
            file_upload = FileUpload.objects.get(pk=pk)

            return Response({
                'id': file_upload.pk,
                'filename': file_upload.original_filename,
                'status': file_upload.upload_status,
                'total_records': file_upload.total_records,
                'successful_records': file_upload.successful_records,
                'failed_records': file_upload.failed_records,
                'processing_summary': file_upload.error_details.get('processing_summary', '') if file_upload.error_details else '',
                'created_at': file_upload.created_at,
                'processing_started_at': file_upload.processing_started_at,
                'processing_completed_at': file_upload.processing_completed_at
            })
        except FileUpload.DoesNotExist:
            return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)


