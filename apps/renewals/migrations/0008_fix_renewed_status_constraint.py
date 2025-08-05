# Generated manually on 2025-08-05 to fix renewed status constraint

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('renewals', '0007_merge_0006_add_renewed_status_0006_delete_caselog'),
    ]

    operations = [
        # Drop the existing constraint
        migrations.RunSQL(
            "ALTER TABLE renewal_cases DROP CONSTRAINT IF EXISTS renewal_cases_status_check;",
            reverse_sql="-- No reverse operation needed"
        ),
        
        # Recreate the constraint with the correct status choices
        migrations.RunSQL(
            """
            ALTER TABLE renewal_cases ADD CONSTRAINT renewal_cases_status_check 
            CHECK (status IN (
                'pending', 'in_progress', 'completed', 'renewed', 'cancelled', 
                'expired', 'due', 'overdue', 'not_required', 'assigned', 
                'failed', 'uploaded'
            ));
            """,
            reverse_sql="ALTER TABLE renewal_cases DROP CONSTRAINT renewal_cases_status_check;"
        ),
    ]
