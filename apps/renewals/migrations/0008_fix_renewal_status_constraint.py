# Generated manually to fix renewal status constraint
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('renewals', '0007_add_workflow_renewal_status_choices'),
    ]

    operations = [
        # Remove the old constraint
        migrations.RunSQL(
            sql="ALTER TABLE renewal_cases DROP CONSTRAINT IF EXISTS renewal_cases_status_check;",
            reverse_sql="-- Cannot reverse constraint drop"
        ),
        
        # Add the new constraint with all status choices
        migrations.RunSQL(
            sql="""
                ALTER TABLE renewal_cases ADD CONSTRAINT renewal_cases_status_check 
                CHECK (status IN (
                    'pending',
                    'in_progress', 
                    'completed',
                    'cancelled',
                    'expired',
                    'due',
                    'overdue',
                    'not_required',
                    'assigned',
                    'failed',
                    'uploaded'
                ));
            """,
            reverse_sql="ALTER TABLE renewal_cases DROP CONSTRAINT IF EXISTS renewal_cases_status_check;"
        ),
    ]
