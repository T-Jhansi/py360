# Generated manually on 2025-07-31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('renewals', '0002_initial'),
    ]

    operations = [
        # Step 1: Remove channel_source field if it exists
        migrations.RunSQL(
            "ALTER TABLE renewal_cases DROP COLUMN IF EXISTS channel_source;",
            reverse_sql="ALTER TABLE renewal_cases ADD COLUMN channel_source VARCHAR(100);"
        ),

        # Step 2: Rename channel column to channel_id (if it exists as a text field)
        migrations.RunSQL(
            """
            DO $$
            BEGIN
                -- Check if channel column exists and is not already a foreign key
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'renewal_cases'
                    AND column_name = 'channel'
                    AND data_type IN ('character varying', 'text')
                ) THEN
                    -- Drop the old channel column
                    ALTER TABLE renewal_cases DROP COLUMN channel;
                END IF;

                -- Add channel_id as foreign key if it doesn't exist
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'renewal_cases'
                    AND column_name = 'channel_id'
                ) THEN
                    ALTER TABLE renewal_cases ADD COLUMN channel_id INTEGER;
                    ALTER TABLE renewal_cases ADD CONSTRAINT renewal_cases_channel_id_fkey
                        FOREIGN KEY (channel_id) REFERENCES channel(id) ON DELETE SET NULL;
                END IF;
            END $$;
            """,
            reverse_sql="ALTER TABLE renewal_cases DROP COLUMN IF EXISTS channel_id;"
        ),

        # Step 3: Create index for channel_id
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS renewal_cas_channel_id_idx ON renewal_cases (channel_id);",
            reverse_sql="DROP INDEX IF EXISTS renewal_cas_channel_id_idx;"
        ),
    ]
