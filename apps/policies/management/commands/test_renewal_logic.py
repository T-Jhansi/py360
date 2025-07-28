from django.core.management.base import BaseCommand
from apps.policies.models import Policy
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Test renewal date logic and display renewal information'

    def handle(self, *args, **options):
        self.stdout.write("🧪 Testing Policy Renewal Logic")
        self.stdout.write("=" * 50)
        
        # Get some sample policies
        policies = Policy.objects.all()[:5]
        
        if not policies:
            self.stdout.write(self.style.WARNING("⚠️ No policies found in database"))
            return
        
        today = date.today()
        
        for policy in policies:
            self.stdout.write(f"\n📋 Policy: {policy.policy_number}")
            self.stdout.write(f"   Customer: {policy.customer.first_name} {policy.customer.last_name}")
            self.stdout.write(f"   Start Date: {policy.start_date}")
            self.stdout.write(f"   End Date: {policy.end_date}")
            self.stdout.write(f"   Renewal Reminder Days: {policy.renewal_reminder_days}")
            
            # Calculate renewal date
            calculated_renewal = policy.calculate_renewal_date()
            self.stdout.write(f"   Calculated Renewal Date: {calculated_renewal}")
            self.stdout.write(f"   Stored Renewal Date: {policy.renewal_date}")
            
            # Check renewal status
            if policy.is_due_for_renewal:
                self.stdout.write(self.style.ERROR("   🚨 DUE FOR RENEWAL"))
            else:
                days_until = policy.days_until_renewal
                if days_until is not None:
                    if days_until > 0:
                        self.stdout.write(f"   ⏰ Renewal in {days_until} days")
                    else:
                        self.stdout.write(f"   ⚠️ Renewal overdue by {abs(days_until)} days")
            
            # Check expiry status
            days_until_expiry = policy.days_until_expiry
            if days_until_expiry is not None:
                if days_until_expiry <= 0:
                    self.stdout.write(self.style.ERROR(f"   💀 EXPIRED {abs(days_until_expiry)} days ago"))
                elif days_until_expiry <= 7:
                    self.stdout.write(self.style.WARNING(f"   ⚠️ Expires in {days_until_expiry} days"))
                else:
                    self.stdout.write(f"   ✅ Expires in {days_until_expiry} days")
        
        # Summary statistics
        self.stdout.write("\n📊 Renewal Summary")
        self.stdout.write("=" * 30)
        
        total_policies = Policy.objects.count()
        due_for_renewal = Policy.objects.filter(renewal_date__lte=today).count()
        expired_policies = Policy.objects.filter(end_date__lt=today).count()
        
        self.stdout.write(f"Total Policies: {total_policies}")
        self.stdout.write(f"Due for Renewal: {due_for_renewal}")
        self.stdout.write(f"Expired Policies: {expired_policies}")
        
        # Show policies by renewal urgency
        self.stdout.write("\n🚨 Renewal Urgency Breakdown:")
        
        # Overdue renewals
        overdue = Policy.objects.filter(
            renewal_date__lt=today,
            status__in=['active', 'pending']
        ).count()
        
        # Due today
        due_today = Policy.objects.filter(
            renewal_date=today,
            status__in=['active', 'pending']
        ).count()
        
        # Due within 7 days
        due_week = Policy.objects.filter(
            renewal_date__lte=today + timedelta(days=7),
            renewal_date__gt=today,
            status__in=['active', 'pending']
        ).count()
        
        # Due within 30 days
        due_month = Policy.objects.filter(
            renewal_date__lte=today + timedelta(days=30),
            renewal_date__gt=today + timedelta(days=7),
            status__in=['active', 'pending']
        ).count()
        
        self.stdout.write(f"   🔴 Overdue: {overdue}")
        self.stdout.write(f"   🟠 Due Today: {due_today}")
        self.stdout.write(f"   🟡 Due This Week: {due_week}")
        self.stdout.write(f"   🟢 Due This Month: {due_month}")
        
        self.stdout.write(self.style.SUCCESS("\n🎉 Renewal logic testing completed!"))
