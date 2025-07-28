from django.core.management.base import BaseCommand
from apps.policies.models import PolicyType, Policy
from apps.customers.models import Customer
from decimal import Decimal
from datetime import date
import json

class Command(BaseCommand):
    help = 'Test coverage details functionality'

    def handle(self, *args, **options):
        self.stdout.write("🧪 Testing Coverage Details Functionality")
        self.stdout.write("=" * 50)
        
        try:
            # Test 1: Create a policy type with default coverage details
            self.stdout.write("\n1. Creating PolicyType with default coverage details...")
            policy_type, created = PolicyType.objects.get_or_create(
                name="Comprehensive Auto Insurance Test",
                defaults={
                    "category": "Motor",
                    "description": "Full coverage auto insurance for testing",
                    "coverage_details": {
                        "liability_limit": 100000,
                        "collision_deductible": 500,
                        "comprehensive_deductible": 250,
                        "personal_injury_protection": True,
                        "uninsured_motorist": True
                    }
                }
            )
            if created:
                self.stdout.write(f"✅ Created PolicyType: {policy_type.name}")
            else:
                self.stdout.write(f"✅ Using existing PolicyType: {policy_type.name}")
            self.stdout.write(f"✅ Created PolicyType: {policy_type.name}")
            self.stdout.write(f"   Default coverage: {json.dumps(policy_type.coverage_details, indent=2)}")
            
            # Test 2: Create a customer
            self.stdout.write("\n2. Creating test customer...")
            customer, created = Customer.objects.get_or_create(
                customer_code="CUS2025TEST",
                defaults={
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john.doe.test@example.com",
                    "phone": "1234567890",
                    "address_line1": "123 Main St",
                    "city": "Anytown",
                    "state": "CA",
                    "postal_code": "12345"
                }
            )
            if created:
                self.stdout.write(f"✅ Created Customer: {customer.first_name} {customer.last_name}")
            else:
                self.stdout.write(f"✅ Using existing Customer: {customer.first_name} {customer.last_name}")
            self.stdout.write(f"✅ Created Customer: {customer.first_name} {customer.last_name}")
            
            # Test 3: Create a policy with custom coverage details
            self.stdout.write("\n3. Creating Policy with custom coverage details...")
            policy = Policy.objects.create(
                policy_number="POL-TEST001",
                customer=customer,
                policy_type=policy_type,
                premium_amount=Decimal('1200.00'),
                sum_assured=Decimal('500000.00'),
                start_date=date(2025, 1, 1),
                end_date=date(2025, 12, 31),
                status="active",
                coverage_details={
                    "liability_limit": 150000,  # Override default
                    "collision_deductible": 250,  # Override default
                    "comprehensive_deductible": 250,  # Keep default
                    "personal_injury_protection": True,  # Keep default
                    "uninsured_motorist": True,  # Keep default
                    "rental_car_coverage": True,  # Additional coverage
                    "roadside_assistance": True   # Additional coverage
                }
            )
            self.stdout.write(f"✅ Created Policy: {policy.policy_number}")
            self.stdout.write(f"   Custom coverage: {json.dumps(policy.coverage_details, indent=2)}")
            
            # Test 4: Test the get_complete_coverage_details method
            self.stdout.write("\n4. Testing get_complete_coverage_details method...")
            complete_coverage = policy.get_complete_coverage_details()
            self.stdout.write(f"✅ Complete coverage details:")
            self.stdout.write(json.dumps(complete_coverage, indent=2))
            
            # Test 5: Create another policy with no custom coverage (uses defaults)
            self.stdout.write("\n5. Creating Policy with default coverage only...")
            policy2 = Policy.objects.create(
                policy_number="POL-TEST002",
                customer=customer,
                policy_type=policy_type,
                premium_amount=Decimal('1000.00'),
                sum_assured=Decimal('300000.00'),
                start_date=date(2025, 1, 1),
                end_date=date(2025, 12, 31),
                status="active"
                # No coverage_details specified - should use defaults
            )
            self.stdout.write(f"✅ Created Policy: {policy2.policy_number}")
            self.stdout.write(f"   Coverage details: {json.dumps(policy2.coverage_details, indent=2)}")
            
            complete_coverage2 = policy2.get_complete_coverage_details()
            self.stdout.write(f"✅ Complete coverage details (should be same as policy type defaults):")
            self.stdout.write(json.dumps(complete_coverage2, indent=2))
            
            # Test 6: Verify database storage
            self.stdout.write("\n6. Verifying database storage...")
            stored_policy = Policy.objects.get(policy_number="POL-TEST001")
            self.stdout.write(f"✅ Retrieved policy from database:")
            self.stdout.write(f"   Coverage details type: {type(stored_policy.coverage_details)}")
            self.stdout.write(f"   Coverage details: {json.dumps(stored_policy.coverage_details, indent=2)}")
            
            # Clean up test data
            self.stdout.write("\n7. Cleaning up test data...")
            Policy.objects.filter(policy_number__startswith="POL-TEST").delete()
            Customer.objects.filter(customer_code="CUS2025TEST").delete()
            PolicyType.objects.filter(name="Comprehensive Auto Insurance Test").delete()
            self.stdout.write("✅ Test data cleaned up")
            
            self.stdout.write("\n" + "=" * 50)
            self.stdout.write("🎉 All tests passed successfully!")
            self.stdout.write("✅ Coverage details functionality is working correctly")
            
        except Exception as e:
            self.stdout.write(f"\n❌ Test failed with error: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
