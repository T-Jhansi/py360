"""
Management command to update customer profiles based on policy count.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.customers.models import Customer


class Command(BaseCommand):
    help = 'Update customer profiles based on policy count (HNI for >1 policy, Normal for ≤1 policy)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
        
        customers = Customer.objects.all()
        total_customers = customers.count()
        updated_count = 0
        hni_count = 0
        normal_count = 0
        
        self.stdout.write(f'Processing {total_customers} customers...')
        
        with transaction.atomic():
            for customer in customers:
                old_profile = customer.profile
                
                # Update metrics (which includes profile calculation)
                if not dry_run:
                    customer.update_metrics()
                    customer.refresh_from_db()
                else:
                    # Calculate what the profile would be
                    policy_count = customer.policies.filter(is_deleted=False).count()
                    new_profile = 'HNI' if policy_count > 1 else 'Normal'
                    customer.profile = new_profile
                
                if old_profile != customer.profile:
                    updated_count += 1
                    self.stdout.write(
                        f'Customer {customer.customer_code} ({customer.full_name}): '
                        f'{old_profile} → {customer.profile} '
                        f'(Policies: {customer.total_policies})'
                    )
                
                if customer.profile == 'HNI':
                    hni_count += 1
                else:
                    normal_count += 1
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(f'SUMMARY:')
        self.stdout.write(f'Total customers processed: {total_customers}')
        self.stdout.write(f'Profiles updated: {updated_count}')
        self.stdout.write(f'HNI customers: {hni_count}')
        self.stdout.write(f'Normal customers: {normal_count}')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('\nThis was a DRY RUN - no changes were made')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\nSuccessfully updated {updated_count} customer profiles!')
            )
