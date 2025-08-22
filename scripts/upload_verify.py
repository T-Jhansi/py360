import os
import sys
import json
from datetime import datetime

# Ensure project root is on PYTHONPATH and Django settings are set
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'renewal_backend.settings.development')
sys.path.insert(0, os.getcwd())

import django
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone


def main(file_path: str):
    django.setup()

    from django.contrib.auth import get_user_model
    from apps.policy_data.views import FileUploadViewSet
    from apps.uploads.models import FileUpload as UploadsFileUpload
    from apps.files_upload.models import FileUpload as ProcessingFileUpload
    from apps.customers.models import Customer
    from apps.policies.models import Policy, PolicyType
    from apps.renewals.models import RenewalCase
    from apps.channels.models import Channel

    if not os.path.exists(file_path):
        print(json.dumps({"ok": False, "error": f"File not found: {file_path}"}))
        return 1

    User = get_user_model()
    user = User.objects.first()
    if not user:
        print(json.dumps({"ok": False, "error": "No user found in DB to attribute the upload"}))
        return 1

    # Read the Excel as an uploaded file
    with open(file_path, "rb") as f:
        content = f.read()
    upload_name = os.path.basename(file_path)
    uploaded = SimpleUploadedFile(
        name=upload_name,
        content=content,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    viewset = FileUploadViewSet()

    # Calculate hash like the API would
    file_hash = viewset._calculate_file_hash(uploaded)

    # Create the tracking records (uploads_fileupload + file_uploads)
    file_upload_record, uploads_record = viewset._create_file_records(
        uploaded_file=uploaded,
        file_hash=file_hash,
        user=user,
    )

    # Process the uploaded Excel contents
    result = viewset._process_uploaded_excel_file(uploads_record, user, file_upload_record)

    # Gather verification info
    out = {
        "ok": True,
        "processing_result": result,
        "uploads_fileupload_id": str(uploads_record.pk) if uploads_record else None,
        "file_uploads_id": file_upload_record.pk if file_upload_record else None,
        "counts": {
            "customers": Customer.objects.count(),
            "policies": Policy.objects.count(),
            "renewal_cases": RenewalCase.objects.count(),
            "policy_types": PolicyType.objects.count(),
            "channels": Channel.objects.count(),
        },
    }

    # Also show the latest records created around now (best-effort)
    since = (timezone.now() - timezone.timedelta(minutes=5))
    new_customers = list(Customer.objects.filter(created_at__gte=since).values("customer_code", "first_name", "last_name", "email")[:5])
    new_policies = list(Policy.objects.filter(created_at__gte=since).values("policy_number", "status", "premium_amount", "sum_assured")[:5])
    new_renewals = list(RenewalCase.objects.filter(created_at__gte=since).values("case_number", "status", "priority")[:5])

    out["recent"] = {
        "customers": new_customers,
        "policies": new_policies,
        "renewal_cases": new_renewals,
    }

    print(json.dumps(out, default=str))
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "Usage: python scripts/upload_verify.py <path-to-excel>"}))
        sys.exit(1)
    sys.exit(main(sys.argv[1]))

