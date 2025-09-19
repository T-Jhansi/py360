from django.core.management.base import BaseCommand
from django.db import connection
import uuid
from django.utils import timezone


class Command(BaseCommand):
    help = 'Add reply email to database'

    def handle(self, *args, **options):
        try:
            cursor = connection.cursor()
            message_id = str(uuid.uuid4())
            now = timezone.now()
            
            # Get the next ID
            cursor.execute("SELECT MAX(id) FROM email_inbox_messages")
            max_id = cursor.fetchone()[0] or 0
            next_id = max_id + 1
            
            # Insert the reply email
            cursor.execute("""
                INSERT INTO email_inbox_messages (
                    id, message_id, thread_id, in_reply_to, "references",
                    from_email, from_name, to_emails, cc_emails, bcc_emails, reply_to,
                    subject, html_content, text_content, status, is_starred, is_important,
                    is_spam, is_phishing, category, subcategory, priority, sentiment,
                    confidence_score, attachments, attachment_count, tags, received_at,
                    headers, size_bytes, source, source_message_id, created_at, updated_at, is_deleted
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, [
                next_id,
                message_id,
                str(uuid.uuid4()),  # thread_id
                'msg_02cc80118c5c_1758278343@example.com',  # in_reply_to
                'msg_02cc80118c5c_1758278343@example.com',  # references
                'sahinayasin17@gmail.com',
                'Sahina Y',
                '["banuyasin401@gmail.com"]',
                '[]',  # cc_emails
                '[]',  # bcc_emails
                'banuyasin401@gmail.com',  # reply_to
                'this is test email from customer',
                '<p>this is test email from customer</p>',
                'this is test email from customer',
                'unread',
                False,  # is_starred
                False,  # is_important
                False,  # is_spam
                False,  # is_phishing
                'general',
                'reply',  # subcategory
                'normal',
                'neutral',  # sentiment
                0.0,  # confidence_score
                '[]',  # attachments
                0,  # attachment_count
                '[]',  # tags
                now,
                '{"From": "Sahina Y <sahinayasin17@gmail.com>", "To": "banuyasin401@gmail.com", "Subject": "this is test email from customer"}',  # headers
                100,  # size_bytes
                'gmail',  # source
                message_id,  # source_message_id
                now,
                now,
                False
            ])
            
            self.stdout.write(
                self.style.SUCCESS('✅ Reply email added successfully!')
            )
            self.stdout.write(f"   Message ID: {message_id}")
            self.stdout.write(f"   From: sahinayasin17@gmail.com")
            self.stdout.write(f"   To: banuyasin401@gmail.com")
            self.stdout.write(f"   Subject: this is test email from customer")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error: {str(e)}')
            )
