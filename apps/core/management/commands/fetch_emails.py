"""
Management command to fetch emails from Gmail and store them in the database.
"""

import imaplib
import email
import json
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.email_inbox.services import EmailInboxService

class Command(BaseCommand):
    help = 'Fetch emails from Gmail and store them in the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='banuyasin401@gmail.com',
            help='Email address to fetch from'
        )
        parser.add_argument(
            '--password',
            type=str,
            help='App password for Gmail (if not provided, will try to get from EmailAccount)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Maximum number of emails to fetch'
        )

    def handle(self, *args, **options):
        email_address = options['email']
        password = options['password']
        limit = options['limit']
        
        self.stdout.write(f"Fetching emails from {email_address}...")
        
        try:
            # Check if password is provided
            if not password:
                self.stdout.write(
                    self.style.ERROR("Password is required. Use --password option or set it in the command.")
                )
                self.stdout.write("To get Gmail App Password:")
                self.stdout.write("1. Go to Google Account settings")
                self.stdout.write("2. Enable 2-Factor Authentication")
                self.stdout.write("3. Generate an App Password for this application")
                return
            
            # Connect to Gmail IMAP
            mail = imaplib.IMAP4_SSL('imap.gmail.com')
            mail.login(email_address, password)
            mail.select('inbox')
            
            # Search for unread emails
            status, messages = mail.search(None, 'UNSEEN')
            if status != 'OK':
                self.stdout.write(self.style.ERROR("Failed to search emails"))
                return
            
            email_ids = messages[0].split()
            total_emails = len(email_ids)
            
            if total_emails == 0:
                self.stdout.write("No new emails found")
                return
            
            self.stdout.write(f"Found {total_emails} unread emails")
            
            # Process emails (limit to specified number)
            processed_count = 0
            for email_id in email_ids[-limit:]:  # Get the latest emails
                try:
                    # Fetch email
                    status, msg_data = mail.fetch(email_id, '(RFC822)')
                    if status != 'OK':
                        continue
                    
                    # Parse email
                    raw_email = msg_data[0][1]
                    email_message = email.message_from_bytes(raw_email)
                    
                    # Extract email details
                    subject = email_message.get('Subject', '')
                    from_email = email_message.get('From', '')
                    to_email = email_message.get('To', '')
                    date_str = email_message.get('Date', '')
                    
                    # Parse date
                    try:
                        from email.utils import parsedate_to_datetime
                        received_date = parsedate_to_datetime(date_str)
                    except:
                        received_date = timezone.now()
                    
                    # Extract content
                    html_content = ''
                    text_content = ''
                    
                    if email_message.is_multipart():
                        for part in email_message.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get('Content-Disposition', ''))
                            
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
                    
                    # Extract from name
                    from_name = None
                    if '<' in from_email and '>' in from_email:
                        from_name = from_email.split('<')[0].strip().strip('"')
                        from_email = from_email.split('<')[1].split('>')[0].strip()
                    
                    # Store email in database
                    inbox_service = EmailInboxService()
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
                    
                    if result['success']:
                        processed_count += 1
                        self.stdout.write(f"✅ Stored email: {subject[:50]}...")
                    else:
                        self.stdout.write(f"❌ Failed to store email: {result.get('message', 'Unknown error')}")
                    
                except Exception as e:
                    self.stdout.write(f"❌ Error processing email {email_id}: {str(e)}")
                    continue
            
            mail.close()
            mail.logout()
            
            self.stdout.write(
                self.style.SUCCESS(f"Successfully processed {processed_count} emails")
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error fetching emails: {str(e)}")
            )
