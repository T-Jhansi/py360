from django.core.management.base import BaseCommand
from django.db import transaction
from apps.customers.models import Customer


class Command(BaseCommand):
    help = 'Update policy counts for all customers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of customers to process in each batch'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        customers = Customer.objects.all()
        total_customers = customers.count()
        updated_count = 0
        
        self.stdout.write(f'Starting to update policy counts for {total_customers} customers...')
        
        # Process in batches to avoid memory issues
        for i in range(0, total_customers, batch_size):
            batch = customers[i:i + batch_size]
            
            with transaction.atomic():
                for customer in batch:
                    old_count = customer.total_policies
                    customer.update_metrics()
                    new_count = customer.total_policies
                    updated_count += 1
                    
                    if old_count != new_count:
                        self.stdout.write(
                            f'Customer {customer.customer_code}: {old_count} -> {new_count} policies'
                        )
            
            self.stdout.write(f'Processed {min(i + batch_size, total_customers)}/{total_customers} customers...')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated policy counts for {updated_count} customers')
        )
