from django.core.management.base import BaseCommand
from apps.policies.models import Policy
from datetime import timedelta


class Command(BaseCommand):
    help = 'Populate renewal dates for existing policies'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reminder-days',
            type=int,
            default=30,
            help='Number of days before end_date for renewal reminder (default: 30)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )

    def handle(self, *args, **options):
        reminder_days = options['reminder_days']
        dry_run = options['dry_run']
        
        self.stdout.write("🔄 Populating Renewal Dates for Existing Policies")
        self.stdout.write("=" * 60)
        
        # Get all policies without renewal_date
        policies_to_update = Policy.objects.filter(
            renewal_date__isnull=True,
            end_date__isnull=False
        )
        
        total_policies = policies_to_update.count()
        self.stdout.write(f"📊 Found {total_policies} policies to update")
        
        if total_policies == 0:
            self.stdout.write(self.style.SUCCESS("✅ All policies already have renewal dates!"))
            return
        
        updated_count = 0
        
        for policy in policies_to_update:
            # Calculate renewal date
            renewal_date = policy.end_date - timedelta(days=reminder_days)
            
            self.stdout.write(
                f"📋 Policy {policy.policy_number}: "
                f"End Date: {policy.end_date} → "
                f"Renewal Date: {renewal_date}"
            )
            
            if not dry_run:
                policy.renewal_date = renewal_date
                policy.renewal_reminder_days = reminder_days
                policy.save()
                updated_count += 1
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"🔍 DRY RUN: Would update {total_policies} policies. "
                    "Run without --dry-run to apply changes."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"🎉 Successfully updated {updated_count} policies with renewal dates!"
                )
            )
            
        # Show some statistics
        self.stdout.write("\n📈 Renewal Date Statistics:")
        self.stdout.write("-" * 40)
        
        from datetime import date
        today = date.today()
        
        # Policies due for renewal (renewal_date <= today)
        due_for_renewal = Policy.objects.filter(
            renewal_date__lte=today,
            status__in=['active', 'pending']
        ).count()
        
        # Policies expiring soon (within next 7 days)
        expiring_soon = Policy.objects.filter(
            end_date__lte=today + timedelta(days=7),
            end_date__gte=today,
            status__in=['active', 'pending']
        ).count()
        
        self.stdout.write(f"🚨 Policies due for renewal: {due_for_renewal}")
        self.stdout.write(f"⚠️  Policies expiring within 7 days: {expiring_soon}")
