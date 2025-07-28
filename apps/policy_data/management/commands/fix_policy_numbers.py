from django.core.management.base import BaseCommand
from django.db import transaction
from apps.policies.models import Policy
from apps.policy_data.utils import generate_policy_number


class Command(BaseCommand):
    help = 'Fix existing policy numbers to use the correct POL-00001 format'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making actual changes',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompt',
        )

    def handle(self, *args, **options):
        self.stdout.write("🔍 Checking for policies with incorrect format...")
        
        # Find policies that don't follow POL-00001 format
        incorrect_policies = Policy.objects.exclude(policy_number__regex=r'^POL-\d{5}$')
        
        if not incorrect_policies.exists():
            self.stdout.write(self.style.SUCCESS("✅ All policy numbers are already in correct format!"))
            return
        
        self.stdout.write(f"📋 Found {incorrect_policies.count()} policies with incorrect format:")
        
        # Show current incorrect formats
        for policy in incorrect_policies[:10]:  # Show first 10
            self.stdout.write(f"   - {policy.policy_number} (Customer: {policy.customer.full_name})")
        
        if incorrect_policies.count() > 10:
            self.stdout.write(f"   ... and {incorrect_policies.count() - 10} more")
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING("\n🔍 DRY RUN - No changes will be made"))
            return
        
        # Ask for confirmation unless --force is used
        if not options['force']:
            response = input("\n🔧 Do you want to fix these policy numbers? (y/N): ")
            if response.lower() != 'y':
                self.stdout.write(self.style.ERROR("❌ Operation cancelled."))
                return
        
        self.stdout.write("\n🔄 Fixing policy numbers...")
        
        fixed_count = 0
        errors = []

        # Process each policy individually to avoid transaction rollback issues
        for policy in incorrect_policies:
            try:
                with transaction.atomic():
                    old_number = policy.policy_number
                    new_number = generate_policy_number()

                    # Update the policy number
                    policy.policy_number = new_number
                    policy.save()

                    self.stdout.write(f"✅ Fixed: {old_number} → {new_number}")
                    fixed_count += 1

            except Exception as e:
                error_msg = f"❌ Failed to fix {policy.policy_number}: {str(e)}"
                self.stdout.write(self.style.ERROR(error_msg))
                errors.append(error_msg)
        
        self.stdout.write(f"\n📊 Summary:")
        self.stdout.write(self.style.SUCCESS(f"   ✅ Fixed: {fixed_count} policies"))
        if errors:
            self.stdout.write(self.style.ERROR(f"   ❌ Errors: {len(errors)} policies"))
            for error in errors:
                self.stdout.write(f"      {error}")
        
        self.stdout.write(self.style.SUCCESS("\n🎉 Policy number fix completed!"))
