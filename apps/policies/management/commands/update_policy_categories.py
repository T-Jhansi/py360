"""
Management command to update policy type categories based on names.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.policies.models import PolicyType


class Command(BaseCommand):
    help = 'Update policy type categories based on policy names'

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
        
        # Category mapping based on policy type names
        category_mapping = {
            # Motor category
            'Vehicle Insurance': 'Motor',
            'Comprehensive Auto Insurance': 'Motor',
            'Motor Insurance': 'Motor',
            'Car Insurance': 'Motor',
            'Two Wheeler Insurance': 'Motor',
            'Commercial Vehicle Insurance': 'Motor',
            
            # Life category
            'Term Life Insurance': 'Life',
            'Life Insurance Plus': 'Life',
            'Life Insurance': 'Life',
            'Term Insurance': 'Life',
            'Whole Life Insurance': 'Life',
            'ULIP': 'Life',
            
            # Property category
            'Home Shield Insurance': 'Property',
            'Home Insurance': 'Property',
            'Property Insurance': 'Property',
            'Fire Insurance': 'Property',
            'Burglary Insurance': 'Property',
            
            # Health category
            'Health Insurance Family': 'Health',
            'Health Insurance': 'Health',
            'Medical Insurance': 'Health',
            'Critical Illness': 'Health',
            'Personal Accident': 'Health',
            
            # Travel category
            'Travel Insurance Pro': 'Travel',
            'Travel Insurance': 'Travel',
            'International Travel': 'Travel',
            'Domestic Travel': 'Travel',
        }
        
        policy_types = PolicyType.objects.all()
        total_policy_types = policy_types.count()
        updated_count = 0
        
        self.stdout.write(f'Processing {total_policy_types} policy types...')
        
        with transaction.atomic():
            for policy_type in policy_types:
                old_category = getattr(policy_type, 'category', 'Motor')
                new_category = old_category
                
                # Check exact match first
                if policy_type.name in category_mapping:
                    new_category = category_mapping[policy_type.name]
                else:
                    # Check partial matches for flexibility
                    name_lower = policy_type.name.lower()
                    
                    if any(keyword in name_lower for keyword in ['vehicle', 'auto', 'motor', 'car', 'bike', 'wheeler']):
                        new_category = 'Motor'
                    elif any(keyword in name_lower for keyword in ['life', 'term', 'ulip']):
                        new_category = 'Life'
                    elif any(keyword in name_lower for keyword in ['home', 'property', 'fire', 'burglary']):
                        new_category = 'Property'
                    elif any(keyword in name_lower for keyword in ['health', 'medical', 'critical', 'accident']):
                        new_category = 'Health'
                    elif any(keyword in name_lower for keyword in ['travel', 'international', 'domestic']):
                        new_category = 'Travel'
                    else:
                        # Default to Motor if no match found
                        new_category = 'Motor'
                
                if old_category != new_category:
                    updated_count += 1
                    self.stdout.write(
                        f'Policy Type "{policy_type.name}": {old_category} → {new_category}'
                    )
                    
                    if not dry_run:
                        policy_type.category = new_category
                        policy_type.save()
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(f'SUMMARY:')
        self.stdout.write(f'Total policy types processed: {total_policy_types}')
        self.stdout.write(f'Categories updated: {updated_count}')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('\nThis was a DRY RUN - no changes were made')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\nSuccessfully updated {updated_count} policy type categories!')
            )
