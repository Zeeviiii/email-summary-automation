"""
Email Fetcher Module
Handles connecting to IMAP server and fetching emails
"""

import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class EmailFetcher:
    """Fetches emails from IMAP server"""

    def __init__(self, config: Dict):
        """
        Initialize email fetcher

        Args:
            config: Email configuration dictionary
        """
        self.imap_server = config.get('imap_server')
        self.imap_port = config.get('imap_port', 993)
        self.email_address = config.get('email_address')
        self.password = config.get('password')
        self.folder = config.get('folder', 'INBOX')
        self.days_to_check = config.get('days_to_check', 7)
        self.max_emails = config.get('max_emails', 50)
        self.connection = None

    def connect(self) -> bool:
        """
        Connect to IMAP server

        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info(f"Connecting to {self.imap_server}:{self.imap_port}")
            self.connection = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            self.connection.login(self.email_address, self.password)
            logger.info("Successfully connected to email server")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to email server: {e}")
            return False

    def disconnect(self):
        """Disconnect from IMAP server"""
        if self.connection:
            try:
                self.connection.close()
                self.connection.logout()
                logger.info("Disconnected from email server")
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")

    def _decode_header_value(self, value: str) -> str:
        """
        Decode email header value

        Args:
            value: Header value to decode

        Returns:
            Decoded string
        """
        if not value:
            return ""

        decoded_parts = decode_header(value)
        result = []

        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                try:
                    if encoding:
                        result.append(part.decode(encoding))
                    else:
                        result.append(part.decode('utf-8', errors='ignore'))
                except Exception:
                    result.append(part.decode('utf-8', errors='ignore'))
            else:
                result.append(str(part))

        return ''.join(result)

    def _extract_body(self, msg: email.message.Message) -> str:
        """
        Extract email body from message

        Args:
            msg: Email message object

        Returns:
            Email body text
        """
        body = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                if "attachment" not in content_disposition:
                    if content_type == "text/plain":
                        try:
                            payload = part.get_payload(decode=True)
                            if payload:
                                body += payload.decode('utf-8', errors='ignore')
                        except Exception as e:
                            logger.warning(f"Error extracting body part: {e}")
        else:
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    body = payload.decode('utf-8', errors='ignore')
            except Exception as e:
                logger.warning(f"Error extracting body: {e}")

        return body.strip()

    def fetch_emails(self) -> List[Dict]:
        """
        Fetch recent emails from server

        Returns:
            List of email dictionaries
        """
        if not self.connection:
            if not self.connect():
                return []

        emails = []

        try:
            # Select mailbox
            self.connection.select(self.folder)

            # Calculate date range
            since_date = (datetime.now() - timedelta(days=self.days_to_check)).strftime("%d-%b-%Y")

            # Search for emails
            logger.info(f"Searching for emails since {since_date}")
            status, message_ids = self.connection.search(None, f'SINCE {since_date}')

            if status != 'OK':
                logger.error("Failed to search emails")
                return []

            # Get list of email IDs
            email_ids = message_ids[0].split()
            total_emails = len(email_ids)

            logger.info(f"Found {total_emails} emails")

            # Limit number of emails
            email_ids = email_ids[-self.max_emails:] if total_emails > self.max_emails else email_ids

            # Fetch emails
            for email_id in email_ids:
                try:
                    status, msg_data = self.connection.fetch(email_id, '(RFC822)')

                    if status != 'OK':
                        continue

                    # Parse email
                    msg = email.message_from_bytes(msg_data[0][1])

                    # Extract email data
                    email_dict = {
                        'id': email_id.decode(),
                        'subject': self._decode_header_value(msg.get('Subject', '')),
                        'from': self._decode_header_value(msg.get('From', '')),
                        'to': self._decode_header_value(msg.get('To', '')),
                        'date': msg.get('Date', ''),
                        'body': self._extract_body(msg)
                    }

                    emails.append(email_dict)
                    logger.debug(f"Fetched email: {email_dict['subject']}")

                except Exception as e:
                    logger.error(f"Error fetching email {email_id}: {e}")
                    continue

            logger.info(f"Successfully fetched {len(emails)} emails")

        except Exception as e:
            logger.error(f"Error during email fetch: {e}")

        return emails

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
