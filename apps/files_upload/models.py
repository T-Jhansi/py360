from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator

User = get_user_model()

def upload_to_path(instance, filename):
    """Generate upload path for files"""
    return f"uploads/{filename}"

class FileUpload(models.Model):
    """Model to store uploaded Excel file info and processing results."""
    uploaded_file = models.FileField(
        upload_to='uploads/',
        validators=[FileExtensionValidator(allowed_extensions=['csv', 'xlsx'])]
    )
    filename = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField()
    file_type = models.CharField(max_length=100)
    upload_path = models.CharField(max_length=500, blank=True)

    total_records = models.IntegerField(default=0)
    successful_records = models.IntegerField(default=0)
    failed_records = models.IntegerField(default=0)

    upload_status = models.CharField(
        max_length=50,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('partial', 'Partial'),
        ],
        default='pending'
    )

    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_files')
    processing_started_at = models.DateTimeField(null=True, blank=True)
    processing_completed_at = models.DateTimeField(null=True, blank=True)
    processing_result = models.JSONField(null=True, blank=True, default=dict)

    error_details = models.JSONField(null=True, blank=True, default=dict)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_file_uploads')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_file_uploads')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Soft delete fields
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='deleted_file_uploads')

    class Meta:
        db_table = 'file_uploads'
        ordering = ['-created_at']

    def __str__(self):
        return self.original_filename
