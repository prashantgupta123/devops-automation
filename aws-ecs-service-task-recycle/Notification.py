"""Email Notification Module.

Provides robust email notification functionality with:
- SMTP server integration
- HTML email formatting
- File attachment support
- Comprehensive error handling
- Multi-recipient support
"""

import smtplib
import logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import Dict, List, Any
import os

logger = logging.getLogger(__name__)


def send_email(smtp_config: Dict[str, str], email_details: Dict[str, Any], content: str) -> None:
    """
    Send email notification with comprehensive error handling.
    
    Args:
        smtp_config: SMTP server configuration
        email_details: Email recipient and subject details
        content: HTML email content
        
    Raises:
        smtplib.SMTPException: If SMTP operation fails
        ValueError: If invalid email configuration
    """
    logger.info("Initiating email notification")
    
    try:
        message = _build_email_message(smtp_config, email_details, content)
        recipients = _get_all_recipients(email_details)
        
        _send_via_smtp(smtp_config, message, recipients)
        logger.info("Email notification sent successfully")
        
    except Exception as e:
        logger.error(f"Email notification failed: {str(e)}")
        raise


def _build_email_message(smtp_config: Dict[str, str], email_details: Dict[str, Any], content: str) -> MIMEMultipart:
    """Build email message with headers and content."""
    current_date = datetime.now().strftime("%d %B %Y")
    subject = f"{email_details.get('subject_prefix', '')} | {email_details['email_subject']} | {current_date}"
    
    message = MIMEMultipart()
    message['Subject'] = subject
    message['From'] = smtp_config["from_email"]
    message['To'] = ",".join(email_details.get("to", []))
    message['Cc'] = ",".join(email_details.get("cc", []))
    
    # Attach HTML content
    message.attach(MIMEText(content, 'html'))
    
    # Handle attachments if present
    for attachment_path in email_details.get("attachments", []):
        _attach_file(message, attachment_path)
    
    return message


def _get_all_recipients(email_details: Dict[str, Any]) -> List[str]:
    """Extract all email recipients from configuration."""
    recipients = []
    for field in ['to', 'cc', 'bcc']:
        field_value = email_details.get(field, [])
        if isinstance(field_value, list):
            recipients.extend(field_value)
        elif field_value:
            recipients.append(field_value)
    
    if not recipients:
        raise ValueError("No valid email recipients configured")
    
    return recipients


def _send_via_smtp(smtp_config: Dict[str, str], message: MIMEMultipart, recipients: List[str]) -> None:
    """Send email via SMTP server."""
    server = smtplib.SMTP(smtp_config["host"], int(smtp_config["port"]), timeout=30)
    
    try:
        server.starttls()
        
        if smtp_config.get("username"):
            server.login(smtp_config["username"], smtp_config["password"])
        
        server.sendmail(smtp_config["from_email"], recipients, message.as_string())
        
    finally:
        server.quit()


def _attach_file(message: MIMEMultipart, file_path: str) -> None:
    """Attach file to email message."""
    try:
        with open(file_path, 'rb') as f:
            attachment = MIMEApplication(f.read())
        
        filename = os.path.basename(file_path)
        attachment.add_header('Content-Disposition', 'attachment', filename=filename)
        message.attach(attachment)
        
        logger.info(f"File attached: {filename}")
        
    except Exception as e:
        logger.error(f"Failed to attach file {file_path}: {str(e)}")
        raise
