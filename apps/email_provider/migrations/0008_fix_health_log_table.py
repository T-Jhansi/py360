# Generated manually to fix missing columns in health_logs table

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('email_provider', '0007_add_smtp_tls_ssl_fields'),
    ]

    operations = [
        # Add missing is_healthy column if it doesn't exist
        migrations.RunSQL(
            "ALTER TABLE email_provider_health_logs ADD COLUMN IF NOT EXISTS is_healthy BOOLEAN;",
            reverse_sql="ALTER TABLE email_provider_health_logs DROP COLUMN IF EXISTS is_healthy;"
        ),
        # Add missing checked_at column if it doesn't exist
        migrations.RunSQL(
            "ALTER TABLE email_provider_health_logs ADD COLUMN IF NOT EXISTS checked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();",
            reverse_sql="ALTER TABLE email_provider_health_logs DROP COLUMN IF EXISTS checked_at;"
        ),
        # Add missing created_at column if it doesn't exist (some models might expect this)
        migrations.RunSQL(
            "ALTER TABLE email_provider_health_logs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();",
            reverse_sql="ALTER TABLE email_provider_health_logs DROP COLUMN IF EXISTS created_at;"
        ),
        # Add missing updated_at column if it doesn't exist
        migrations.RunSQL(
            "ALTER TABLE email_provider_health_logs ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();",
            reverse_sql="ALTER TABLE email_provider_health_logs DROP COLUMN IF EXISTS updated_at;"
        ),
    ]
