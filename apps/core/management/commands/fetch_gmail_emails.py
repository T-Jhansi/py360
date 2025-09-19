import imaplib
import email
import json
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.email_inbox.services import EmailInboxService


class Command(BaseCommand):
    help = 'Fetch emails from Gmail and store them in the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Gmail email address',
            default='banuyasin401@gmail.com'
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Gmail app password',
            required=True
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Number of emails to fetch',
            default=10
        )
        parser.add_argument(
            '--folder',
            type=str,
            help='Gmail folder to fetch from',
            default='INBOX'
        )

    def handle(self, *args, **options):
        email_address = options['email']
        password = options['password']
        limit = options['limit']
        folder = options['folder']

        self.stdout.write(f"Fetching emails from {email_address}...")

        try:
            # Connect to Gmail
            mail = imaplib.IMAP4_SSL('imap.gmail.com')
            mail.login(email_address, password)
            mail.select(folder)

            # Search for emails
            status, messages = mail.search(None, 'ALL')
            if status != 'OK':
                self.stdout.write(self.style.ERROR('Failed to search emails'))
                return

            email_ids = messages[0].split()
            email_ids = email_ids[-limit:]  # Get the latest emails

            inbox_service = EmailInboxService()
            processed_count = 0

            for email_id in email_ids:
                try:
                    # Fetch email
                    status, msg_data = mail.fetch(email_id, '(RFC822)')
                    if status != 'OK':
                        continue

                    # Parse email
                    raw_email = msg_data[0][1]
                    email_message = email.message_from_bytes(raw_email)

                    # Extract email data
                    from_email = email_message.get('From', '')
                    to_email = email_message.get('To', '')
                    subject = email_message.get('Subject', '')
                    date = email_message.get('Date', '')

                    # Extract body
                    html_content = ''
                    text_content = ''

                    if email_message.is_multipart():
                        for part in email_message.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get('Content-Disposition'))

                            if content_type == 'text/plain' and 'attachment' not in content_disposition:
                                text_content = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            elif content_type == 'text/html' and 'attachment' not in content_disposition:
                                html_content = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    else:
                        content_type = email_message.get_content_type()
                        if content_type == 'text/plain':
                            text_content = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
                        elif content_type == 'text/html':
                            html_content = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')

                    # Extract sender name
                    from_name = ''
                    if '<' in from_email and '>' in from_email:
                        from_name = from_email.split('<')[0].strip().strip('"')
                        from_email = from_email.split('<')[1].split('>')[0].strip()

                    # Store email in database
                    result = inbox_service.receive_email(
                        from_email=from_email,
                        to_email=to_email,
                        subject=subject,
                        html_content=html_content,
                        text_content=text_content,
                        from_name=from_name,
                        raw_headers=dict(email_message.items()),
                        raw_body=raw_email.decode('utf-8', errors='ignore')
                    )

                    if result.get('success'):
                        processed_count += 1
                        self.stdout.write(f"✅ Processed: {subject} from {from_email}")
                    else:
                        self.stdout.write(self.style.WARNING(f"⚠️ Failed to process: {subject} - {result.get('message')}"))

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Error processing email {email_id}: {str(e)}"))
                    continue

            mail.close()
            mail.logout()

            self.stdout.write(
                self.style.SUCCESS(f"✅ Successfully processed {processed_count} emails from Gmail")
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error connecting to Gmail: {str(e)}"))
            self.stdout.write(
                self.style.WARNING(
                    "Make sure you're using an App Password, not your regular Gmail password.\n"
                    "To create an App Password:\n"
                    "1. Go to Google Account settings\n"
                    "2. Security → 2-Step Verification → App passwords\n"
                    "3. Generate a new app password for 'Mail'\n"
                    "4. Use that password with this command"
                )
            )
