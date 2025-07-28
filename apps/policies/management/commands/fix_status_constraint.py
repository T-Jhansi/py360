from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Fix policy status constraint to include new status choices'

    def handle(self, *args, **options):
        self.stdout.write('🔧 Fixing policy status constraint...')
        
        try:
            with connection.cursor() as cursor:
                # Drop existing constraint
                self.stdout.write('📝 Dropping existing constraint...')
                cursor.execute("""
                    ALTER TABLE policies DROP CONSTRAINT IF EXISTS policies_status_check;
                """)
                
                # Add new constraint with all status choices
                self.stdout.write('✅ Adding new constraint with updated status choices...')
                cursor.execute("""
                    ALTER TABLE policies ADD CONSTRAINT policies_status_check 
                    CHECK (status IN (
                        'active',
                        'expired', 
                        'cancelled',
                        'pending',
                        'suspended',
                        'expiring_soon',
                        'pre_due',
                        'reinstatement',
                        'policy_due'
                    ));
                """)
                
                # Verify the constraint
                self.stdout.write('🔍 Verifying constraint...')
                cursor.execute("""
                    SELECT conname, pg_get_constraintdef(oid) as definition
                    FROM pg_constraint 
                    WHERE conrelid = 'policies'::regclass 
                    AND conname = 'policies_status_check';
                """)
                
                result = cursor.fetchone()
                if result:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Constraint updated successfully!')
                    )
                    self.stdout.write(f'📋 Constraint: {result[0]}')
                    self.stdout.write(f'📝 Definition: {result[1]}')
                else:
                    self.stdout.write(
                        self.style.ERROR('❌ Failed to verify constraint')
                    )
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error fixing constraint: {str(e)}')
            )
            return
            
        self.stdout.write(
            self.style.SUCCESS('🎉 Policy status constraint fixed successfully!')
        )
        self.stdout.write('📋 New allowed status values:')
        self.stdout.write('   - active, expired, cancelled, pending, suspended')
        self.stdout.write('   - expiring_soon, pre_due, reinstatement, policy_due')
        self.stdout.write('')
        self.stdout.write('🚀 You can now upload Excel files with the new status logic!')
