"""
Output Handler Module
Handles saving and sending email summaries
"""

import os
import json
from datetime import datetime
from typing import Dict, List
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


class OutputHandler:
    """Handles output of email summaries"""

    def __init__(self, config: Dict):
        """
        Initialize output handler

        Args:
            config: Output configuration dictionary
        """
        self.output_dir = config.get('output_dir', 'summaries')
        self.format = config.get('format', 'txt')
        self.send_email = config.get('send_email', False)
        self.recipient_email = config.get('recipient_email')

        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logger.info(f"Created output directory: {self.output_dir}")

    def save_summary(self, summary: str, emails: List[Dict]) -> str:
        """
        Save summary to file

        Args:
            summary: Summary text
            emails: List of email dictionaries

        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if self.format == 'txt':
            filepath = self._save_as_txt(summary, timestamp)
        elif self.format == 'json':
            filepath = self._save_as_json(summary, emails, timestamp)
        elif self.format == 'html':
            filepath = self._save_as_html(summary, emails, timestamp)
        else:
            logger.warning(f"Unsupported format: {self.format}, defaulting to txt")
            filepath = self._save_as_txt(summary, timestamp)

        logger.info(f"Summary saved to: {filepath}")
        return filepath

    def _save_as_txt(self, summary: str, timestamp: str) -> str:
        """Save summary as plain text"""
        filepath = os.path.join(self.output_dir, f"summary_{timestamp}.txt")

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(summary)

        return filepath

    def _save_as_json(self, summary: str, emails: List[Dict], timestamp: str) -> str:
        """Save summary as JSON"""
        filepath = os.path.join(self.output_dir, f"summary_{timestamp}.json")

        data = {
            'timestamp': datetime.now().isoformat(),
            'email_count': len(emails),
            'summary': summary,
            'emails': [
                {
                    'subject': email.get('subject'),
                    'from': email.get('from'),
                    'date': email.get('date')
                }
                for email in emails
            ]
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return filepath

    def _save_as_html(self, summary: str, emails: List[Dict], timestamp: str) -> str:
        """Save summary as HTML"""
        filepath = os.path.join(self.output_dir, f"summary_{timestamp}.html")

        html_content = f"""
<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>סיכום מיילים - {timestamp}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        .metadata {{
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .summary {{
            line-height: 1.8;
            white-space: pre-wrap;
        }}
        .footer {{
            margin-top: 30px;
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>סיכום מיילים</h1>

        <div class="metadata">
            <strong>תאריך יצירה:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
            <strong>מספר מיילים:</strong> {len(emails)}
        </div>

        <div class="summary">
{summary}
        </div>

        <div class="footer">
            נוצר על ידי מערכת אוטומציה לסיכום מיילים
        </div>
    </div>
</body>
</html>
"""

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return filepath

    def send_summary_email(self, summary: str, email_config: Dict) -> bool:
        """
        Send summary via email

        Args:
            summary: Summary text
            email_config: Email configuration

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.send_email or not self.recipient_email:
            return False

        try:
            msg = MIMEMultipart()
            msg['From'] = email_config.get('email_address')
            msg['To'] = self.recipient_email
            msg['Subject'] = f"סיכום מיילים - {datetime.now().strftime('%Y-%m-%d')}"

            body = f"""
שלום,

להלן סיכום המיילים שהתקבלו:

{summary}

---
נוצר אוטומטית על ידי מערכת סיכום מיילים
"""

            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            # Send email
            with smtplib.SMTP_SSL(email_config.get('imap_server').replace('imap', 'smtp'), 465) as server:
                server.login(email_config.get('email_address'), email_config.get('password'))
                server.send_message(msg)

            logger.info(f"Summary email sent to {self.recipient_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send summary email: {e}")
            return False
