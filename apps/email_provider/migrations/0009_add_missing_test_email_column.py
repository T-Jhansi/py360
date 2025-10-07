# Generated manually to fix missing test_email column

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('email_provider', '0008_fix_health_log_table'),
    ]

    operations = [
        migrations.RunSQL(
            "ALTER TABLE email_provider_test_results ADD COLUMN IF NOT EXISTS test_email VARCHAR(254);",
            reverse_sql="ALTER TABLE email_provider_test_results DROP COLUMN IF EXISTS test_email;"
        ),
    ]
