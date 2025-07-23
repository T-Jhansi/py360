from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.uploads.models import UploadsFileupload
from apps.customers.models import Customer
from apps.policies.models import Policy
from apps.renewals.models import RenewalCase
from apps.files_upload.models import FileUpload
from apps.policy_data.views import FileUploadViewSet

User = get_user_model()

class Command(BaseCommand):
    help = 'Test Excel processing for the latest uploaded file'

    def handle(self, *args, **options):
        self.stdout.write("🔍 Testing Excel processing...")
        
        try:
            # Get latest upload
            latest_upload = UploadsFileupload.objects.latest('created_at')
            self.stdout.write(f"📁 Latest upload: {latest_upload.filename}")
            self.stdout.write(f"📊 Current status: {latest_upload.upload_status}")
            
            # Get user
            user = User.objects.first()
            if not user:
                self.stdout.write(self.style.ERROR("❌ No user found!"))
                return
                
            self.stdout.write(f"👤 Using user: {user.email}")
            
            # Check counts before
            customers_before = Customer.objects.count()
            policies_before = Policy.objects.count()
            renewals_before = RenewalCase.objects.count()
            
            self.stdout.write(f"\n📈 Before processing:")
            self.stdout.write(f"   - Customers: {customers_before}")
            self.stdout.write(f"   - Policies: {policies_before}")
            self.stdout.write(f"   - Renewal Cases: {renewals_before}")
            
            # Process the Excel file
            viewset = FileUploadViewSet()
            
            self.stdout.write(f"\n🔄 Processing Excel file...")
            result = viewset._process_uploaded_excel_file(latest_upload, user)
            
            self.stdout.write(self.style.SUCCESS(f"✅ Processing result: {result}"))
            
            # Check counts after
            customers_after = Customer.objects.count()
            policies_after = Policy.objects.count()
            renewals_after = RenewalCase.objects.count()
            
            self.stdout.write(f"\n📈 After processing:")
            self.stdout.write(f"   - Customers: {customers_after} (+{customers_after - customers_before})")
            self.stdout.write(f"   - Policies: {policies_after} (+{policies_after - policies_before})")
            self.stdout.write(f"   - Renewal Cases: {renewals_after} (+{renewals_after - renewals_before})")
            
            # Show recent records
            recent_customers = Customer.objects.filter(created_at__gte=latest_upload.created_at)
            if recent_customers.exists():
                self.stdout.write(f"\n👥 New customers created:")
                for customer in recent_customers:
                    self.stdout.write(f"   - {customer.customer_code}: {customer.first_name} {customer.last_name} ({customer.email})")
            
            recent_policies = Policy.objects.filter(created_at__gte=latest_upload.created_at)
            if recent_policies.exists():
                self.stdout.write(f"\n📋 New policies created:")
                for policy in recent_policies:
                    self.stdout.write(f"   - {policy.policy_number}: {policy.policy_type.name}")
            
            recent_renewals = RenewalCase.objects.filter(created_at__gte=latest_upload.created_at)
            if recent_renewals.exists():
                self.stdout.write(f"\n🔄 New renewal cases created:")
                for renewal in recent_renewals:
                    self.stdout.write(f"   - {renewal.case_number}: {renewal.customer.first_name} - {renewal.status}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {e}"))
            import traceback
            self.stdout.write(self.style.ERROR(f"❌ Traceback: {traceback.format_exc()}"))
