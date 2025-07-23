import pandas as pd
import hashlib
import os
from datetime import datetime, date
from decimal import Decimal
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage

from apps.customers.models import Customer
from apps.files_upload.models import FileUpload
from apps.uploads.models import FileUpload as UploadsFileUpload
from apps.policies.models import Policy, PolicyType
from .serializers import (
    FileUploadSerializer,
    EnhancedFileUploadSerializer,
    FileUploadRequestSerializer
)
from apps.policy_data.utils import generate_customer_code, generate_case_number, generate_policy_number

User = get_user_model()

class FileUploadViewSet(viewsets.ModelViewSet):
    """Enhanced file upload viewset with comprehensive Excel processing"""

    queryset = FileUpload.objects.all()
    serializer_class = FileUploadSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """Upload and process Excel file with enhanced validation"""
        try:
            # Step 1: Get uploaded file
            uploaded_file = request.FILES.get('file') or request.FILES.get('upload_file')

            if not uploaded_file:
                return Response({'error': 'No file provided.'}, status=status.HTTP_400_BAD_REQUEST)

            # Step 2: File validation
            validation_result = self._validate_file(uploaded_file)

            if not validation_result['valid']:
                return Response({
                    'error': validation_result['error'],
                    'details': validation_result.get('details', {})
                }, status=status.HTTP_400_BAD_REQUEST)

            # Step 3: Calculate file hash
            file_hash = self._calculate_file_hash(uploaded_file)

            # Step 4: Check for duplicates
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

            # Step 5: Create file records
            try:
                file_upload_record, uploads_record = self._create_file_records(
                    uploaded_file, file_hash, request.user
                )
            except Exception as create_error:
                raise create_error

            # Step 6: Process Excel file content
            try:
                # Process Excel directly using the uploads_record file
                processing_result = self._process_uploaded_excel_file(uploads_record, request.user, file_upload_record)
            except Exception as process_error:
                # Update status to failed
                uploads_record.status = 'failed'
                uploads_record.error_message = str(process_error)
                uploads_record.save()

                # Update file_uploads record
                if file_upload_record:
                    file_upload_record.upload_status = 'failed'
                    file_upload_record.error_details = {'error': str(process_error), 'type': 'processing_error'}
                    file_upload_record.processing_completed_at = timezone.now()
                    file_upload_record.updated_by = request.user
                    file_upload_record.save()
                raise process_error

            # Step 7: Prepare response
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

            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            # Comprehensive error logging
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
        # Temporarily allow more file types for testing
        allowed_extensions = ['.xlsx', '.xls', '.csv', '.txt']
        allowed_mime_types = [
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-excel',
            'text/csv',
            'text/plain'
        ]

        file_extension = os.path.splitext(file.name)[1].lower()

        # Check file extension
        if file_extension not in allowed_extensions:
            return {
                'valid': False,
                'error': 'Invalid file type. Only Excel files (.xlsx, .xls) are allowed.',
                'details': {'file_extension': file_extension, 'allowed_extensions': allowed_extensions}
            }

        # Check file size (max 50MB)
        max_file_size = 50 * 1024 * 1024  # 50MB
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

        # Check MIME type
        if hasattr(file, 'content_type') and file.content_type not in allowed_mime_types:
            return {
                'valid': False,
                'error': 'Invalid file content type.',
                'details': {'content_type': file.content_type, 'allowed_types': allowed_mime_types}
            }

        # Additional security: Check file signature (magic bytes)
        try:
            file.seek(0)
            header = file.read(8)
            file.seek(0)

            # Excel file signatures
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
            # Generate secure filename
            secure_filename = self._generate_secure_filename(uploaded_file.name, user.id)

            # First create record in uploads.FileUpload
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
                    updated_by=user,
                    metadata={
                        'upload_source': 'policy_data_import',
                        'upload_timestamp': timezone.now().isoformat(),
                        'user_id': user.id,
                        'user_email': user.email,
                        'secure_filename': secure_filename,
                        'virus_scan_required': True
                    }
                )

                # Create FileUpload record
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

        # Get file extension
        file_extension = os.path.splitext(original_filename)[1].lower()

        # Generate secure filename
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
                total_records=0,  # Will be updated after processing
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
                updated_by=user
            )
            return file_upload_record
        except Exception as e:
            raise e

    def _process_uploaded_excel_file(self, uploads_record, user, file_upload_record=None):
        """Process Excel file directly from uploads_record"""
        try:
            # Read Excel file directly from uploads_record
            df = pd.read_excel(uploads_record.file.path)

            # Validate required columns (make it more flexible)
            validation_result = self._validate_excel_structure_flexible(df)
            if not validation_result['valid']:
                uploads_record.status = 'failed'
                uploads_record.error_message = validation_result['error']
                uploads_record.save()
                return validation_result

            # Process data
            processing_result = self._process_excel_data(df, user)

            # Update uploads_record with results
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

            # Update file_uploads record with results
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
            uploads_record.save()
            raise e

    def _validate_excel_structure_flexible(self, df):
        """Flexible validation for Excel file structure"""
        # Core required columns for customer data
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


        return {'valid': True}

    def _process_excel_file(self, file_upload_record, uploads_record, user):
        """Process Excel file and extract data"""
        try:
            # Read Excel file
            df = pd.read_excel(file_upload_record.uploaded_file.path)

            # Validate required columns
            validation_result = self._validate_excel_structure(df)
            if not validation_result['valid']:
                self._mark_processing_failed(
                    file_upload_record, uploads_record, validation_result['error']
                )
                return validation_result

            # Process data
            processing_result = self._process_excel_data(df, user)

            # Update file records with results
            self._update_file_records_with_results(
                file_upload_record, uploads_record, processing_result
            )

            return processing_result

        except Exception as e:
            error_msg = f"Excel processing error: {str(e)}"
            self._mark_processing_failed(file_upload_record, uploads_record, error_msg)
            return {'error': error_msg, 'valid': False}

    def _validate_excel_structure(self, df):
        """Validate Excel file structure"""
        required_columns = [
            'first_name', 'last_name', 'email', 'phone', 'date_of_birth',
            'gender', 'address', 'kyc_status', 'kyc_documents',
            'communication_preferences', 'policy_number', 'policy_type',
            'premium_amount', 'start_date', 'end_date', 'nominee_name',
            'nominee_relationship', 'agent_name', 'agent_code',
            'priority', 'renewal_amount', 'payment_status',
            'last_contact_date', 'notes'
        ]

        # Check for communication_attempts column (accept both variations)
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

        # Process each row individually with its own transaction
        for idx, (_, row) in enumerate(df.iterrows()):
            try:
                with transaction.atomic():
                    # Process customer data
                    customer, customer_created = self._process_customer_data(row, user)
                    if customer_created:
                        created_customers += 1

                    # Process policy data
                    policy, policy_created = self._process_policy_data(row, customer, user)
                    if policy_created:
                        created_policies += 1

                    # Process renewal case data
                    self._process_renewal_case_data(row, customer, policy, user)
                    created_renewal_cases += 1

                    successful_records += 1

            except Exception as e:
                failed_records += 1
                error_msg = f"Row {idx + 1}: {str(e)}"
                errors.append(error_msg)
                # Log detailed error for debugging

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
        # Check if customer exists by email
        customer = Customer.objects.filter(email=row['email']).first()
        customer_created = False

        if not customer:
            # Create new customer
            customer_code = generate_customer_code()

            # Parse priority from Excel or use default
            priority = str(row.get('priority', 'medium')).lower()
            if priority not in ['low', 'medium', 'high', 'urgent']:
                priority = 'medium'

            customer = Customer.objects.create(
                customer_code=customer_code,
                first_name=row['first_name'],
                last_name=row['last_name'],
                email=row['email'],
                phone=str(row.get('phone', '')),
                date_of_birth=self._parse_date(row.get('date_of_birth')),
                gender=row.get('gender', 'male').lower() if row.get('gender') else 'male',
                address=str(row.get('address', '')),
                kyc_status=row.get('kyc_status', 'pending').lower(),
                kyc_documents=str(row.get('kyc_documents', '')),
                communication_preferences=str(row.get('communication_preferences', '')),
                priority=priority,
                created_by=user,
                updated_by=user
            )
            customer_created = True
        return customer, customer_created

    def _process_policy_data(self, row, customer, user):
        """Process policy data from Excel row"""
        policy_number = str(row.get('policy_number', f'POL{customer.customer_code}'))

        # Check if policy exists
        policy = Policy.objects.filter(policy_number=policy_number).first()
        policy_created = False

        if not policy:
            # Get or create policy type
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

            # Parse payment frequency
            payment_frequency = str(row.get('payment_frequency', 'yearly')).lower()
            if payment_frequency not in ['monthly', 'quarterly', 'half_yearly', 'yearly']:
                payment_frequency = 'yearly'

            # Parse policy status
            policy_status = str(row.get('status', 'active')).lower()
            if policy_status not in ['active', 'expired', 'cancelled', 'pending', 'suspended']:
                policy_status = 'active'

            # Create new policy
            policy = Policy.objects.create(
                policy_number=policy_number,
                customer=customer,
                policy_type=policy_type,
                start_date=self._parse_date(row.get('start_date')),
                end_date=self._parse_date(row.get('end_date')),
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

    def _process_renewal_case_data(self, row, customer, policy, user):
        """Process renewal case data from Excel row"""

        case_number = generate_case_number()

        # Parse renewal case status
        renewal_status = str(row.get('status', 'pending')).lower()
        if renewal_status not in ['pending', 'in_progress', 'completed', 'cancelled', 'expired']:
            renewal_status = 'pending'

        # Parse priority
        renewal_priority = str(row.get('priority', 'medium')).lower()
        if renewal_priority not in ['low', 'medium', 'high', 'urgent']:
            renewal_priority = 'medium'

        # Parse payment status
        payment_status = str(row.get('payment_status', 'pending')).lower()
        if payment_status not in ['pending', 'completed', 'failed', 'refunded']:
            payment_status = 'pending'

        # Get renewal amount from Excel or use policy premium
        renewal_amount = row.get('renewal_amount')
        if renewal_amount is None or pd.isna(renewal_amount):
            renewal_amount = policy.premium_amount
        else:
            renewal_amount = Decimal(str(renewal_amount))

        # Determine assigned_to user
        assigned_to_id = None
        if 'assigned_to' in row and row['assigned_to']:
            # Try to find user by email, employee_id, or ID
            assigned_to_value = str(row['assigned_to']).strip()
            from django.contrib.auth import get_user_model
            from django.db import models
            User = get_user_model()

            # Try to find user by ID first (if it's a number)
            if assigned_to_value.isdigit():
                try:
                    assigned_user = User.objects.get(id=int(assigned_to_value))
                    assigned_to_id = assigned_user.pk
                except User.DoesNotExist:
                    assigned_user = None

            # If not found by ID, try by email or employee_id
            if not assigned_to_id:
                assigned_user = User.objects.filter(
                    models.Q(email=assigned_to_value) | models.Q(employee_id=assigned_to_value)
                ).first()
                if assigned_user:
                    assigned_to_id = assigned_user.pk

        # If no assigned_to specified or user not found, assign to the uploader
        if not assigned_to_id:
            assigned_to_id = user.id

        # Create renewal case using raw SQL
        from django.db import connection
        from django.utils import timezone
        now = timezone.now()

        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO renewal_cases (
                    case_number, customer_id, policy_id, status, priority,
                    renewal_amount, payment_status, payment_date,
                    communication_attempts, last_contact_date, notes,
                    assigned_to, created_by_id, updated_by_id, created_at, updated_at,
                    is_deleted, deleted_at, deleted_by_id
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, [
                case_number, customer.pk, policy.id,
                renewal_status,
                renewal_priority,
                renewal_amount,
                payment_status,
                self._parse_datetime(row.get('payment_date')),
                int(row.get('communication_attempts') or row.get('communications_attempts', 0)) if (row.get('communication_attempts') or row.get('communications_attempts')) else 0,
                self._parse_datetime(row.get('last_contact_date')),
                str(row.get('notes', '')),
                assigned_to_id, user.id, user.id, now, now,
                False, None, None
            ])

        # Create a dummy renewal_case object for return
        renewal_case = type('RenewalCase', (), {
            'case_number': case_number,
            'customer': customer,
            'policy': policy
        })()

        return renewal_case

    def _parse_date(self, date_value):
        """Parse date from various formats"""
        if pd.isna(date_value) or date_value is None:
            return None

        if isinstance(date_value, (date, datetime)):
            return date_value.date() if isinstance(date_value, datetime) else date_value

        # Try to parse string dates
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

        # Try to parse string datetimes
        try:
            return pd.to_datetime(datetime_value)
        except:
            return None

    def _update_file_records_with_results(self, file_upload_record, uploads_record, result):
        """Update file records with processing results"""
        # Update files_upload.FileUpload (now that processing_result is TEXT)
        file_upload_record.total_records = result['total_records']
        file_upload_record.successful_records = result['successful_records']
        file_upload_record.failed_records = result['failed_records']
        file_upload_record.upload_status = 'completed' if result['failed_records'] == 0 else 'partial'
        file_upload_record.processing_completed_at = timezone.now()

        # Store result summary in error_details field
        import json

        result_summary = {
            'processing_summary': f"Processing completed. Total: {result['total_records']}, Success: {result['successful_records']}, Failed: {result['failed_records']}",
            'total_records': result['total_records'],
            'successful_records': result['successful_records'],
            'failed_records': result['failed_records'],
            'errors': result.get('errors', [])[:3],  # First 3 errors
            'status': 'completed' if result['failed_records'] == 0 else 'partial',
            'created_customers': result.get('created_customers', 0),
            'created_policies': result.get('created_policies', 0),
            'created_renewal_cases': result.get('created_renewal_cases', 0)
        }

        file_upload_record.error_details = result_summary
        file_upload_record.processing_result = json.dumps(result_summary)  # Convert to JSON string
        file_upload_record.save()

        # Update uploads.FileUpload
        uploads_record.status = 'completed' if result['failed_records'] == 0 else 'failed'
        uploads_record.error_message = result_summary['processing_summary']
        uploads_record.processing_result = json.dumps(result_summary)  # Convert to JSON string
        uploads_record.updated_by = file_upload_record.updated_by
        uploads_record.save(update_fields=['status', 'error_message', 'processing_result', 'updated_by'])

    def _mark_processing_failed(self, file_upload_record, uploads_record, error_msg):
        """Mark processing as failed for both records"""
        import json

        # Create failure result
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

        # Update files_upload.FileUpload
        file_upload_record.upload_status = 'failed'
        file_upload_record.error_details = failure_result
        file_upload_record.processing_result = json.dumps(failure_result)
        file_upload_record.processing_completed_at = timezone.now()
        file_upload_record.save()

        # Update uploads.FileUpload
        uploads_record.status = 'failed'
        uploads_record.error_message = error_msg
        uploads_record.processing_result = json.dumps(failure_result)
        uploads_record.save(update_fields=['status', 'error_message', 'processing_result'])

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get processing status of uploaded file"""
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


