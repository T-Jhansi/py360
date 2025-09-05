from rest_framework import serializers
from .models import FileUpload
import os


class FileUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)

    class Meta:
        model = FileUpload
        fields = ['file', 'filename', 'original_filename', 'file_size', 'file_type', 'upload_status']
        read_only_fields = ['file_name', 'original_filename', 'file_size', 'file_type', 'upload_status']

    def validate_file(self, value):
        """Validate uploaded file to ensure it's CSV or XLSX format"""
        if not value:
            raise serializers.ValidationError("No file provided.")
        
        # Get file extension
        file_extension = os.path.splitext(value.name)[1].lower()
        
        # Check file extension
        allowed_extensions = ['.csv', '.xlsx']
        if file_extension not in allowed_extensions:
            raise serializers.ValidationError(
                f"Only CSV and XLSX files are supported. "
                f"Please upload a file with .csv or .xlsx extension. "
                f"Your file has extension: {file_extension}"
            )
        
        # Check file size (optional - limit to 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File size too large. Maximum allowed size is 10MB. "
                f"Your file size is: {value.size / (1024*1024):.2f}MB"
            )
        
        # Additional validation for XLSX files (check file signature)
        if file_extension == '.xlsx':
            try:
                # Reset file pointer to beginning
                value.seek(0)
                file_header = value.read(4)
                value.seek(0)  # Reset again for normal processing
                
                # XLSX files start with PK (ZIP signature)
                if not file_header.startswith(b'PK'):
                    raise serializers.ValidationError(
                        "Invalid XLSX file. The file does not appear to be a valid Excel file."
                    )
            except Exception as e:
                # If header check fails, still allow the file
                pass
        
        return value

    def create(self, validated_data):
        uploaded_file = validated_data.pop('file')

        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)  
        
        upload_path = os.path.join(upload_dir, uploaded_file.name)
        
        with open(upload_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        file_instance = FileUpload.objects.create(
            uploaded_file=uploaded_file,
            filename=uploaded_file.name,
            original_filename=uploaded_file.name,
            file_size=uploaded_file.size,
            file_type=os.path.splitext(uploaded_file.name)[1],
            upload_path=upload_path,
            uploaded_by=self.context['request'].user,
            **validated_data
        )

        return file_instance


class FileUploadListSerializer(serializers.ModelSerializer):
    """Serializer for listing file upload details"""

    file_size_formatted = serializers.SerializerMethodField()
    processing_duration = serializers.SerializerMethodField()
    success_rate = serializers.SerializerMethodField()
    uploaded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = FileUpload
        fields = [
            'id',
            'original_filename',
            'file_size',
            'file_size_formatted',
            'upload_status',
            'total_records',
            'successful_records',
            'failed_records',
            'success_rate',
            'processing_duration',
            'uploaded_by_name',
            'processing_started_at',
            'processing_completed_at',
            'created_at',
            'updated_at',
            'error_details'
        ]
        read_only_fields = fields

    def get_file_size_formatted(self, obj):
        """Format file size in human readable format"""
        if not obj.file_size:
            return "0 B"

        size = obj.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def get_processing_duration(self, obj):
        """Calculate processing duration in seconds"""
        if obj.processing_started_at and obj.processing_completed_at:
            duration = obj.processing_completed_at - obj.processing_started_at
            return duration.total_seconds()
        return None

    def get_success_rate(self, obj):
        """Calculate success rate percentage"""
        if obj.total_records and obj.total_records > 0:
            return round((obj.successful_records / obj.total_records) * 100, 2)
        return 0.0

    def get_uploaded_by_name(self, obj):
        """Get the name of the user who uploaded the file"""
        if obj.uploaded_by:
            return f"{obj.uploaded_by.first_name} {obj.uploaded_by.last_name}".strip() or obj.uploaded_by.email
        return "Unknown"


class FileUploadDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for individual file upload"""

    file_size_formatted = serializers.SerializerMethodField()
    processing_duration = serializers.SerializerMethodField()
    success_rate = serializers.SerializerMethodField()
    uploaded_by_details = serializers.SerializerMethodField()
    created_by_details = serializers.SerializerMethodField()
    updated_by_details = serializers.SerializerMethodField()

    class Meta:
        model = FileUpload
        fields = [
            'id',
            'filename',
            'original_filename',
            'file_size',
            'file_size_formatted',
            'file_type',
            'upload_path',
            'upload_status',
            'total_records',
            'successful_records',
            'failed_records',
            'success_rate',
            'processing_duration',
            'uploaded_by_details',
            'created_by_details',
            'updated_by_details',
            'processing_started_at',
            'processing_completed_at',
            'processing_result',
            'error_details',
            'created_at',
            'updated_at',
            'is_deleted',
            'deleted_at'
        ]
        read_only_fields = fields

    def get_file_size_formatted(self, obj):
        """Format file size in human readable format"""
        if not obj.file_size:
            return "0 B"

        size = obj.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def get_processing_duration(self, obj):
        """Calculate processing duration in seconds"""
        if obj.processing_started_at and obj.processing_completed_at:
            duration = obj.processing_completed_at - obj.processing_started_at
            return duration.total_seconds()
        return None

    def get_success_rate(self, obj):
        """Calculate success rate percentage"""
        if obj.total_records and obj.total_records > 0:
            return round((obj.successful_records / obj.total_records) * 100, 2)
        return 0.0

    def get_uploaded_by_details(self, obj):
        """Get detailed info about the user who uploaded the file"""
        if obj.uploaded_by:
            return {
                'id': obj.uploaded_by.id,
                'email': obj.uploaded_by.email,
                'name': f"{obj.uploaded_by.first_name} {obj.uploaded_by.last_name}".strip() or obj.uploaded_by.email
            }
        return None

    def get_created_by_details(self, obj):
        """Get detailed info about the user who created the record"""
        if obj.created_by:
            return {
                'id': obj.created_by.id,
                'email': obj.created_by.email,
                'name': f"{obj.created_by.first_name} {obj.created_by.last_name}".strip() or obj.created_by.email
            }
        return None

    def get_updated_by_details(self, obj):
        """Get detailed info about the user who last updated the record"""
        if obj.updated_by:
            return {
                'id': obj.updated_by.id,
                'email': obj.updated_by.email,
                'name': f"{obj.updated_by.first_name} {obj.updated_by.last_name}".strip() or obj.updated_by.email
            }
        return None
