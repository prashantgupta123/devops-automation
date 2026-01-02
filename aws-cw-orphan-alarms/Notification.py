"""Email Notification Module.

Provides email notification functionality with SMTP support.
"""

import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml

logger = logging.getLogger(__name__)


class EmailNotifier:
    """Email notification service for sending reports."""
    
    def __init__(self, config_path: str = "inputs.yml"):
        """
        Initialize email notifier with configuration.
        
        Args:
            config_path: Path to YAML configuration file
        """
        self.config = self._load_config(config_path)
        self.email_config = self.config.get("Email", {}).get("details", {})
    
    @staticmethod
    def _load_config(config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            logger.error("Configuration file not found: %s", config_path)
            raise
        except yaml.YAMLError as e:
            logger.error("Error parsing YAML configuration: %s", e)
            raise
    
    def send_email(
        self, 
        subject: str, 
        body: str, 
        attachment_path: Optional[str] = None
    ) -> None:
        """
        Send email notification with optional attachment.
        
        Args:
            subject: Email subject line (will be prefixed with config subject_prefix)
            body: Email body content (supports HTML)
            attachment_path: Optional path to file attachment
        
        Raises:
            smtplib.SMTPException: If email sending fails
        """
        try:
            message = self._create_message(subject, body, attachment_path)
            self._send_message(message)
            logger.info("Email sent successfully: %s", subject)
        except Exception as e:
            logger.error("Failed to send email: %s", e)
            raise
    
    def _create_message(
        self, 
        subject: str, 
        body: str, 
        attachment_path: Optional[str]
    ) -> MIMEMultipart:
        """Create email message with headers and content."""
        current_date = datetime.now().strftime("%d %B %Y")
        subject_prefix = self.email_config.get("subject_prefix", "Alert")
        full_subject = f"{subject_prefix} | {subject} | {current_date}"
        
        message = MIMEMultipart()
        message['Subject'] = full_subject
        message['From'] = self.email_config["from"]
        message['To'] = ",".join(self.email_config["to"])
        message['CC'] = ",".join(self.email_config.get("cc", []))
        
        # Attach body
        message.attach(MIMEText(body, 'html'))
        
        # Attach file if provided
        if attachment_path and Path(attachment_path).exists():
            self._attach_file(message, attachment_path)
        
        return message
    
    @staticmethod
    def _attach_file(message: MIMEMultipart, file_path: str) -> None:
        """Attach file to email message."""
        with open(file_path, 'rb') as file:
            attachment = MIMEApplication(file.read())
            filename = Path(file_path).name
            attachment.add_header(
                'Content-Disposition', 
                'attachment', 
                filename=filename
            )
            message.attach(attachment)
    
    def _send_message(self, message: MIMEMultipart) -> None:
        """Send email message via SMTP."""
        smtp_host = self.email_config["host"]
        smtp_username = self.email_config.get("username")
        smtp_password = self.email_config.get("password")
        
        with smtplib.SMTP(smtp_host) as server:
            server.starttls()
            
            if smtp_username:
                server.login(smtp_username, smtp_password)
            
            recipients = self._get_all_recipients(message)
            server.sendmail(message['From'], recipients, message.as_string())
    
    @staticmethod
    def _get_all_recipients(message: MIMEMultipart) -> List[str]:
        """Extract all recipients from message headers."""
        to_recipients = message['To'].split(",") if message['To'] else []
        cc_recipients = message['CC'].split(",") if message['CC'] else []
        return to_recipients + cc_recipients
