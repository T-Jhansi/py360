import imaplib
import email
import json
from django.core.management.base import BaseCommand
from apps.email_inbox.services import EmailInboxService
from apps.email_inbox.models import EmailInboxMessage
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fetch reply emails from Gmail using IMAP'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Gmail email address')
        parser.add_argument('--password', type=str, help='Gmail app password')
        parser.add_argument('--limit', type=int, default=10, help='Number of emails to fetch')

    def handle(self, *args, **options):
        email_address = options['email']
        password = options['password']
        limit = options['limit']

        if not email_address or not password:
            self.stdout.write(
                self.style.ERROR('Please provide email and password')
            )
            return
        
        # Use the new SendGrid account email if not provided
        if not email_address:
            email_address = 'sahinyasin2000@gmail.com'

        try:
            # Connect to Gmail IMAP
            mail = imaplib.IMAP4_SSL('imap.gmail.com')
            mail.login(email_address, password)
            mail.select('inbox')

            # Search for unread emails
            status, messages = mail.search(None, 'UNSEEN')
            
            if status != 'OK':
                self.stdout.write(
                    self.style.ERROR('Failed to search emails')
                )
                return

            email_ids = messages[0].split()
            fetched_count = 0

            for email_id in email_ids[-limit:]:  # Get latest emails
                try:
                    # Fetch email
                    status, msg_data = mail.fetch(email_id, '(RFC822)')
                    
                    if status != 'OK':
                        continue

                    # Parse email
                    email_body = msg_data[0][1]
                    email_message = email.message_from_bytes(email_body)

                    # Extract email details
                    from_email = email_message.get('From', '')
                    to_email = email_message.get('To', '')
                    subject = email_message.get('Subject', '')
                    date = email_message.get('Date', '')

                    # Get email content
                    text_content = ''
                    html_content = ''

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

                    # Check if this is a reply to our emails
                    if 'replies@13.233.6.207' in to_email or 'banuyasin401@gmail.com' in to_email:
                        # Check if we already have this email
                        existing_email = EmailInboxMessage.objects.filter(
                            from_email=from_email,
                            subject=subject,
                            received_at__date=email.utils.parsedate_to_datetime(date).date() if date else None
                        ).first()

                        if not existing_email:
                            # Store the email
                            inbox_service = EmailInboxService()
                            result = inbox_service.receive_email(
                                from_email=from_email,
                                to_email=to_email,
                                subject=subject,
                                text_content=text_content,
                                html_content=html_content,
                                from_name=email.utils.parseaddr(from_email)[0] or '',
                                reply_to='banuyasin401@gmail.com'
                            )

                            if result.get('success'):
                                fetched_count += 1
                                self.stdout.write(
                                    self.style.SUCCESS(f'✅ Fetched reply: {subject} from {from_email}')
                                )
                            else:
                                self.stdout.write(
                                    self.style.ERROR(f'❌ Failed to store: {subject}')
                                )

                except Exception as e:
                    logger.error(f'Error processing email {email_id}: {str(e)}')
                    continue

            mail.close()
            mail.logout()

            self.stdout.write(
                self.style.SUCCESS(f'🎉 Successfully fetched {fetched_count} reply emails')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error connecting to Gmail: {str(e)}')
            )
