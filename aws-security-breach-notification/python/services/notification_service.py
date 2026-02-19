"""Notification service for security events via SES email."""

import boto3
from typing import Dict, Any, List
from core.event_types import EventDetail
from core.enums import EventType
from core.settings import get_config
from core.exceptions import NotificationError
from utils.logger import setup_logger
from utils.aws_helpers import extract_user_from_event

logger = setup_logger(__name__)

# Lambda function events are informational, not security breaches
_INFO_EVENTS = {
    "CreateFunction20150331",
    "UpdateFunctionConfiguration20150331v2",
    "UpdateFunctionCode20150331v2",
}


class NotificationService:
    """Generates and sends HTML email alerts for security events."""

    def __init__(self, event: Dict[str, Any], event_details: List[EventDetail]):
        detail = event['detail']
        identity = detail['userIdentity']
        
        config = get_config()

        self.event = event
        self.event_details = event_details
        self.account_id = identity["accountId"]
        self.account_name = config.account_name
        self.user_type = identity.get('type', 'Unknown')
        self.user = extract_user_from_event(event)
        self.event_region = detail["awsRegion"]
        self.event_name = detail['eventName']
        self.event_id = event['id']
        self.event_time = event['time']
        self.layer_version = config.layer_version

        self.event_type = (
            EventType.INFO if self.event_name in _INFO_EVENTS else EventType.EVENT
        )

        # Build the human-readable summary from handler-provided titles
        self.event_title = '\n'.join(
            d.get('title', f"Event {self.event_name} detected")
            for d in self.event_details
        )

        # Recipients: configured emails + the acting user (unless Root)
        self.email_recipients = config.email_ids
        if self.user != "Root":
            self.email_recipients += f",{self.user}"
        
        self.config = config

    def send_email(self) -> bool:
        """
        Send the alert email via SES.
        
        Returns:
            True on success, False on failure
        
        Raises:
            NotificationError: If email sending fails critically
        """
        try:
            recipients = [
                e.strip() for e in self.email_recipients.split(',') if e.strip()
            ]
            if not recipients:
                logger.warning("No email recipients configured")
                return False

            subject = self._build_subject()
            body = self._build_html_body()

            ses_kwargs: Dict[str, Any] = {'region_name': self.config.ses_region}
            if self.config.ses_access_key != 'NA':
                ses_kwargs['aws_access_key_id'] = self.config.ses_access_key
                ses_kwargs['aws_secret_access_key'] = self.config.ses_secret_key

            ses = boto3.client('ses', **ses_kwargs)
            response = ses.send_email(
                Destination={'ToAddresses': recipients},
                Message={
                    'Body': {'Html': {'Charset': 'UTF-8', 'Data': body}},
                    'Subject': {'Charset': 'UTF-8', 'Data': subject},
                },
                Source=self.config.ses_source_email,
            )

            logger.info(f"Email sent. MessageId: {response['MessageId']}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}", exc_info=True)
            return False

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_subject(self) -> str:
        if self.event_type == EventType.INFO:
            prefix = f"AWS Security | {self.event_title} |"
        else:
            prefix = "AWS Security Breach |"
        return f"{prefix} {self.event_name} | {self.account_name} | {self.account_id}"

    def _build_html_body(self) -> str:
        resource_rows = ""
        for detail in self.event_details:
            for key, value in detail.items():
                if key == 'title':
                    continue  # title is shown in the header, not the table
                label = key.replace('_', ' ').title()
                resource_rows += (
                    f'<tr>'
                    f'<td style="font-weight:normal;border:1px solid black;padding:5px">{label}</td>'
                    f'<td style="font-weight:normal;border:1px solid black;padding:5px" align="right">{value}</td>'
                    f'</tr>'
                )

        return f"""
<html>
<head><title>AWS Security Alert</title></head>
<body style="font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;margin:0;padding:20px;background-color:#f6f4f4">
  <table style="width:600px;margin:0 auto;background-color:white;border-collapse:collapse">
    <tr>
      <td style="padding:25px 35px">
        <table style="width:100%;border-collapse:collapse">
          <tr>
            <td style="width:80%">
              <h2 style="color:#343b41;margin:0">[Alerting] Security Breach Notification</h2>
            </td>
            <td style="width:20%;text-align:right">
              <img src="https://cdn-icons-png.flaticon.com/512/18266/18266546.png" height="60" width="60" />
            </td>
          </tr>
        </table>

        <pre style="font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;font-size:16px;line-height:1.5;white-space:pre-wrap;word-wrap:break-word">{self.event_title}</pre>

        <table style="width:100%;border:1px solid black;border-collapse:collapse;margin-top:20px">
          <tr><th colspan="2" style="font-weight:bold;border:1px solid black;padding:8px;background-color:#f0f0f0">Event Details</th></tr>
          {self._meta_row("AWS Account ID", self.account_id)}
          {self._meta_row("AWS Account Name", self.account_name)}
          {self._meta_row("User", self.user)}
          {self._meta_row("User Type", self.user_type)}
          {self._meta_row("Event Region", self.event_region)}
          {self._meta_row("Event Name", self.event_name)}
          {self._meta_row("Event Time", self.event_time)}
          {self._meta_row("Event ID", self.event_id)}
          {self._meta_row("Layer Version", self.layer_version)}
        </table>

        <table style="width:100%;border:1px solid black;border-collapse:collapse;margin-top:20px">
          <tr><th colspan="2" style="font-weight:bold;border:1px solid black;padding:8px;background-color:#f0f0f0">Resource Details</th></tr>
          {resource_rows}
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    @staticmethod
    def _meta_row(label: str, value: Any) -> str:
        return (
            f'<tr>'
            f'<td style="font-weight:normal;border:1px solid black;padding:5px">{label}</td>'
            f'<td style="font-weight:normal;border:1px solid black;padding:5px" align="right">{value}</td>'
            f'</tr>'
        )
