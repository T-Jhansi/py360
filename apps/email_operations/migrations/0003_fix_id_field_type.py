# Generated manually to fix ID field type mismatch

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('email_operations', '0002_add_missing_fields'),
    ]

    operations = [
        # Since the table is empty, we can safely drop and recreate it
        migrations.RunSQL(
            """
            -- Drop all dependent tables first
            DROP TABLE IF EXISTS email_tracking CASCADE;
            DROP TABLE IF EXISTS email_webhooks CASCADE;
            DROP TABLE IF EXISTS email_automation_logs CASCADE;
            DROP TABLE IF EXISTS email_delivery_reports CASCADE;
            DROP TABLE IF EXISTS email_analytics CASCADE;
            DROP TABLE IF EXISTS email_queue CASCADE;
            DROP TABLE IF EXISTS email_messages CASCADE;
            """,
            reverse_sql="-- Cannot reverse this operation safely"
        ),
        
        # Recreate the email_messages table with correct UUID primary key
        migrations.RunSQL(
            """
            CREATE TABLE email_messages (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                message_id VARCHAR(255) UNIQUE NOT NULL,
                to_email VARCHAR(254) NOT NULL,
                cc_emails JSONB DEFAULT '[]'::jsonb,
                bcc_emails JSONB DEFAULT '[]'::jsonb,
                from_email VARCHAR(254) NOT NULL,
                from_name VARCHAR(100),
                reply_to VARCHAR(254),
                subject VARCHAR(500) NOT NULL,
                html_content TEXT,
                text_content TEXT,
                template_id UUID,
                template_name VARCHAR(200),
                template_variables JSONB DEFAULT '{}'::jsonb,
                priority VARCHAR(10) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
                status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'sending', 'sent', 'delivered', 'failed', 'bounced', 'complained', 'unsubscribed')),
                scheduled_at TIMESTAMP WITH TIME ZONE,
                sent_at TIMESTAMP WITH TIME ZONE,
                campaign_id VARCHAR(100),
                tags JSONB DEFAULT '[]'::jsonb,
                provider_name VARCHAR(100),
                provider_message_id VARCHAR(255),
                error_message TEXT,
                retry_count INTEGER DEFAULT 0 CHECK (retry_count >= 0),
                max_retries INTEGER DEFAULT 3 CHECK (max_retries >= 0),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                created_by_id INTEGER REFERENCES users_user(id) ON DELETE SET NULL,
                updated_by_id INTEGER REFERENCES users_user(id) ON DELETE SET NULL,
                is_deleted BOOLEAN DEFAULT FALSE,
                deleted_at TIMESTAMP WITH TIME ZONE,
                deleted_by_id INTEGER REFERENCES users_user(id) ON DELETE SET NULL
            );
            """,
            reverse_sql="-- Cannot reverse this operation safely"
        ),
        
        # Create indexes
        migrations.RunSQL(
            """
            CREATE INDEX email_messages_status_priority_idx ON email_messages (status, priority);
            CREATE INDEX email_messages_to_email_status_idx ON email_messages (to_email, status);
            CREATE INDEX email_messages_campaign_id_status_idx ON email_messages (campaign_id, status);
            CREATE INDEX email_messages_scheduled_at_status_idx ON email_messages (scheduled_at, status);
            CREATE INDEX email_messages_created_at_status_idx ON email_messages (created_at, status);
            """,
            reverse_sql="-- Cannot reverse this operation safely"
        ),
        
        # Recreate other tables with proper UUID foreign keys
        migrations.RunSQL(
            """
            CREATE TABLE email_queue (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email_message_id UUID NOT NULL REFERENCES email_messages(id) ON DELETE CASCADE,
                priority VARCHAR(10) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
                status VARCHAR(20) DEFAULT 'queued' CHECK (status IN ('queued', 'processing', 'sent', 'failed', 'cancelled')),
                scheduled_for TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                processed_at TIMESTAMP WITH TIME ZONE,
                attempts INTEGER DEFAULT 0 CHECK (attempts >= 0),
                max_attempts INTEGER DEFAULT 3 CHECK (max_attempts >= 0),
                error_message TEXT,
                last_error TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            reverse_sql="-- Cannot reverse this operation safely"
        ),
        
        migrations.RunSQL(
            """
            CREATE TABLE email_tracking (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email_message_id UUID NOT NULL REFERENCES email_messages(id) ON DELETE CASCADE,
                event_type VARCHAR(20) NOT NULL CHECK (event_type IN ('sent', 'delivered', 'opened', 'clicked', 'bounced', 'complained', 'unsubscribed', 'blocked')),
                event_data JSONB DEFAULT '{}'::jsonb,
                ip_address INET,
                user_agent TEXT,
                location VARCHAR(100),
                link_url VARCHAR(200),
                link_text VARCHAR(500),
                event_time TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            reverse_sql="-- Cannot reverse this operation safely"
        ),
        
        migrations.RunSQL(
            """
            CREATE TABLE email_delivery_reports (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email_message_id UUID NOT NULL REFERENCES email_messages(id) ON DELETE CASCADE,
                provider_name VARCHAR(100) NOT NULL,
                provider_message_id VARCHAR(255) NOT NULL,
                status VARCHAR(20) NOT NULL CHECK (status IN ('delivered', 'bounced', 'complained', 'unsubscribed', 'blocked', 'deferred', 'dropped')),
                status_message TEXT,
                response_time DOUBLE PRECISION,
                raw_data JSONB DEFAULT '{}'::jsonb,
                reported_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            reverse_sql="-- Cannot reverse this operation safely"
        ),
        
        migrations.RunSQL(
            """
            CREATE TABLE email_analytics (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                date DATE NOT NULL,
                period_type VARCHAR(20) DEFAULT 'daily' CHECK (period_type IN ('daily', 'weekly', 'monthly', 'yearly')),
                campaign_id VARCHAR(100),
                template_id UUID,
                emails_sent INTEGER DEFAULT 0 CHECK (emails_sent >= 0),
                emails_delivered INTEGER DEFAULT 0 CHECK (emails_delivered >= 0),
                emails_opened INTEGER DEFAULT 0 CHECK (emails_opened >= 0),
                emails_clicked INTEGER DEFAULT 0 CHECK (emails_clicked >= 0),
                emails_bounced INTEGER DEFAULT 0 CHECK (emails_bounced >= 0),
                emails_complained INTEGER DEFAULT 0 CHECK (emails_complained >= 0),
                emails_unsubscribed INTEGER DEFAULT 0 CHECK (emails_unsubscribed >= 0),
                delivery_rate DOUBLE PRECISION DEFAULT 0.0,
                open_rate DOUBLE PRECISION DEFAULT 0.0,
                click_rate DOUBLE PRECISION DEFAULT 0.0,
                bounce_rate DOUBLE PRECISION DEFAULT 0.0,
                complaint_rate DOUBLE PRECISION DEFAULT 0.0,
                unsubscribe_rate DOUBLE PRECISION DEFAULT 0.0,
                avg_response_time DOUBLE PRECISION DEFAULT 0.0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                UNIQUE(date, period_type, campaign_id, template_id)
            );
            """,
            reverse_sql="-- Cannot reverse this operation safely"
        ),
        
        # Create indexes for other tables
        migrations.RunSQL(
            """
            CREATE INDEX email_queue_status_scheduled_for_idx ON email_queue (status, scheduled_for);
            CREATE INDEX email_queue_priority_scheduled_for_idx ON email_queue (priority, scheduled_for);
            CREATE INDEX email_tracking_email_message_event_type_idx ON email_tracking (email_message_id, event_type);
            CREATE INDEX email_tracking_event_type_event_time_idx ON email_tracking (event_type, event_time);
            CREATE INDEX email_delivery_reports_email_message_status_idx ON email_delivery_reports (email_message_id, status);
            CREATE INDEX email_delivery_reports_provider_name_status_idx ON email_delivery_reports (provider_name, status);
            CREATE INDEX email_analytics_date_period_type_idx ON email_analytics (date, period_type);
            CREATE INDEX email_analytics_campaign_id_date_idx ON email_analytics (campaign_id, date);
            CREATE INDEX email_analytics_template_id_date_idx ON email_analytics (template_id, date);
            """,
            reverse_sql="-- Cannot reverse this operation safely"
        ),
    ]
