from django.core.management.base import BaseCommand
from apps.policies.models import Policy, PolicyType
from datetime import timedelta, date


class Command(BaseCommand):
    help = 'Configure renewal reminder days for policies (15, 30, 45, or 60 days before end_date)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reminder-days',
            type=int,
            choices=[15, 30, 45, 60],
            default=30,
            help='Number of days before end_date to start renewal process (choices: 15, 30, 45, 60)'
        )
        parser.add_argument(
            '--policy-type',
            type=str,
            help='Apply to specific policy type only (e.g., "Life Insurance", "Motor")'
        )
        parser.add_argument(
            '--category',
            type=str,
            choices=['Motor', 'Life', 'Property', 'Health', 'Travel'],
            help='Apply to specific category only'
        )
        parser.add_argument(
            '--policy-ids',
            type=str,
            help='Comma-separated list of specific policy IDs to update'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )

    def handle(self, *args, **options):
        reminder_days = options['reminder_days']
        policy_type = options['policy_type']
        category = options['category']
        policy_ids = options['policy_ids']
        dry_run = options['dry_run']
        
        self.stdout.write("🔧 Configuring Renewal Reminder Days")
        self.stdout.write("=" * 50)
        self.stdout.write(f"📅 Setting renewal reminders to: {reminder_days} days before end_date")
        
        # Build query filters
        filters = {'end_date__isnull': False}
        
        if policy_ids:
            # Specific policy IDs
            ids = [int(id.strip()) for id in policy_ids.split(',')]
            filters['id__in'] = ids
            self.stdout.write(f"🎯 Target: Specific policies {ids}")
        else:
            # Filter by policy type or category
            if policy_type:
                filters['policy_type__name__icontains'] = policy_type
                self.stdout.write(f"🎯 Target: Policy type containing '{policy_type}'")
            elif category:
                filters['policy_type__category'] = category
                self.stdout.write(f"🎯 Target: Category '{category}'")
            else:
                self.stdout.write("🎯 Target: All policies")
        
        # Get policies to update
        policies_to_update = Policy.objects.filter(**filters)
        total_policies = policies_to_update.count()
        
        if total_policies == 0:
            self.stdout.write(self.style.WARNING("⚠️ No policies found matching the criteria"))
            return
        
        self.stdout.write(f"📊 Found {total_policies} policies to update")
        
        # Show breakdown by current reminder days
        current_breakdown = {}
        for policy in policies_to_update:
            current_days = policy.renewal_reminder_days
            current_breakdown[current_days] = current_breakdown.get(current_days, 0) + 1
        
        self.stdout.write("\n📈 Current Renewal Reminder Days Distribution:")
        for days, count in sorted(current_breakdown.items()):
            self.stdout.write(f"   {days} days: {count} policies")
        
        # Preview changes
        self.stdout.write(f"\n🔄 Changes Preview:")
        updated_count = 0
        
        for policy in policies_to_update[:10]:  # Show first 10 as preview
            old_renewal_date = policy.renewal_date
            new_renewal_date = policy.end_date - timedelta(days=reminder_days)
            
            self.stdout.write(
                f"📋 {policy.policy_number} ({policy.policy_type.name}): "
                f"End: {policy.end_date} | "
                f"Old Renewal: {old_renewal_date} | "
                f"New Renewal: {new_renewal_date}"
            )
            
            if not dry_run:
                policy.renewal_reminder_days = reminder_days
                policy.renewal_date = new_renewal_date
                policy.save()
                updated_count += 1
        
        # Update remaining policies if not dry run
        if not dry_run and total_policies > 10:
            remaining_policies = policies_to_update[10:]
            for policy in remaining_policies:
                policy.renewal_reminder_days = reminder_days
                policy.renewal_date = policy.end_date - timedelta(days=reminder_days)
                policy.save()
                updated_count += 1
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"\n🔍 DRY RUN: Would update {total_policies} policies. "
                    "Run without --dry-run to apply changes."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n🎉 Successfully updated {updated_count} policies!"
                )
            )
        
        # Show renewal urgency after changes
        self.stdout.write("\n📊 Renewal Urgency After Changes:")
        self.stdout.write("-" * 40)
        
        today = date.today()
        urgency_data = Policy.get_policies_by_renewal_urgency()
        
        self.stdout.write(f"🔴 Overdue: {urgency_data['overdue'].count()}")
        self.stdout.write(f"🟠 Due Today: {urgency_data['due_today'].count()}")
        self.stdout.write(f"🟡 Due This Week: {urgency_data['due_this_week'].count()}")
        self.stdout.write(f"🟢 Due This Month: {urgency_data['due_this_month'].count()}")
        
        # Show recommended actions
        self.stdout.write("\n💡 Recommended Actions:")
        if urgency_data['overdue'].count() > 0:
            self.stdout.write("   🚨 Contact overdue renewals immediately")
        if urgency_data['due_today'].count() > 0:
            self.stdout.write("   📞 Follow up on today's due renewals")
        if urgency_data['due_this_week'].count() > 0:
            self.stdout.write("   📧 Send renewal notices for this week's due policies")
        
        self.stdout.write(self.style.SUCCESS("\n✅ Renewal reminder configuration completed!"))
