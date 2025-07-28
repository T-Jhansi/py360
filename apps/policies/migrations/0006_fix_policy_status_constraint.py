# Generated manually to fix policy status constraint
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('policies', '0005_add_additional_policy_status_choices'),
    ]

    operations = [
        # Remove the old constraint
        migrations.RunSQL(
            sql="ALTER TABLE policies DROP CONSTRAINT IF EXISTS policies_status_check;",
            reverse_sql="-- Cannot reverse constraint drop"
        ),
        
        # Add the new constraint with all status choices
        migrations.RunSQL(
            sql="""
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
            """,
            reverse_sql="ALTER TABLE policies DROP CONSTRAINT IF EXISTS policies_status_check;"
        ),
    ]
