from django.core.management.base import BaseCommand
from apps.policy_data.utils import generate_batch_code
from apps.renewals.models import RenewalCase
import re


class Command(BaseCommand):
    help = 'Test batch code generation functionality'

    def handle(self, *args, **options):
        self.stdout.write("🧪 Testing Batch Code Generation")
        self.stdout.write("=" * 50)
        
        # Test 1: Generate first batch code of the day
        self.stdout.write("\n1️⃣ Testing first batch code generation...")
        batch_code_1 = generate_batch_code()
        self.stdout.write(f"   Generated: {batch_code_1}")
        
        # Test 2: Generate second batch code (should be next letter)
        self.stdout.write("\n2️⃣ Testing second batch code generation...")
        batch_code_2 = generate_batch_code()
        self.stdout.write(f"   Generated: {batch_code_2}")
        
        # Test 3: Check format
        self.stdout.write("\n3️⃣ Checking batch code format...")
        pattern = r'^BATCH-\d{4}-\d{2}-\d{2}-[A-Z]+$'
        
        for i, code in enumerate([batch_code_1, batch_code_2], 1):
            if re.match(pattern, code):
                self.stdout.write(self.style.SUCCESS(f"   ✅ Batch code {i} format is correct: {code}"))
            else:
                self.stdout.write(self.style.ERROR(f"   ❌ Batch code {i} format is incorrect: {code}"))
        
        # Test 4: Check uniqueness
        self.stdout.write("\n4️⃣ Checking batch code uniqueness...")
        if batch_code_1 != batch_code_2:
            self.stdout.write(self.style.SUCCESS("   ✅ Batch codes are unique"))
            self.stdout.write(f"      First:  {batch_code_1}")
            self.stdout.write(f"      Second: {batch_code_2}")
        else:
            self.stdout.write(self.style.ERROR(f"   ❌ Batch codes are not unique: {batch_code_1}"))
        
        # Test 5: Check existing renewal cases
        self.stdout.write("\n5️⃣ Checking existing renewal cases...")
        renewal_cases = RenewalCase.objects.all()
        self.stdout.write(f"   Total renewal cases: {renewal_cases.count()}")
        
        if renewal_cases.exists():
            self.stdout.write("   Recent renewal cases with batch codes:")
            for case in renewal_cases[:5]:
                self.stdout.write(f"      {case.case_number}: {case.batch_code}")
        
        self.stdout.write(self.style.SUCCESS("\n🎉 Batch code testing completed!"))
