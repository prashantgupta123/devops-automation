"""AWS GuardDuty Lambda Function Handler.

Processes GuardDuty findings from EventBridge and sends notifications
via multiple channels including SNS, Email, and Google Chat.

Environment Variables:
    SNS_TOPIC_ARN: ARN of SNS topic for notifications
    GOOGLE_CHAT_WEBHOOK: Google Chat webhook URL
    ENABLE_SNS: Enable SNS notifications (true/false)
    ENABLE_EMAIL: Enable email notifications (true/false) 
    ENABLE_CHAT: Enable Google Chat notifications (true/false)
"""

import json
import os
import logging
from typing import Dict, Any
import requests
from AWSSession import get_aws_session
from Notification import send_email

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Process GuardDuty findings and send multi-channel notifications.
    
    Args:
        event: EventBridge event containing GuardDuty finding
        context: Lambda context object
        
    Returns:
        Dict containing response status and details
    """
    logger.info("Processing GuardDuty finding notification")
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Load configuration
        logger.info("Loading configuration from input.json")
        config = _load_configuration()
        logger.info("Configuration loaded successfully")
        
        # Extract finding details
        logger.info("Extracting finding data from event")
        finding_data = _extract_finding_data(event)
        logger.info(f"Finding data extracted: {json.dumps(finding_data)}")
        
        # Send notifications based on configuration
        logger.info("Starting notification delivery")
        notification_results = _send_notifications(config, finding_data)
        logger.info(f"Notification results: {json.dumps(notification_results)}")
        
        logger.info("GuardDuty notification processing completed successfully")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Notifications processed successfully',
                'results': notification_results,
                'finding_id': finding_data['finding_id']
            })
        }
        
    except Exception as e:
        logger.error(f"Failed to process GuardDuty notification: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Notification processing failed',
                'message': str(e)
            })
        }


def _load_configuration() -> Dict[str, Any]:
    """Load configuration from input.json file."""
    try:
        with open('input.json', 'r') as f:
            config = json.load(f)
            logger.info("Configuration file read successfully")
            return config
    except Exception as e:
        logger.error(f"Failed to load configuration: {str(e)}")
        raise


def _extract_finding_data(event: Dict[str, Any]) -> Dict[str, Any]:
    """Extract relevant data from GuardDuty finding event."""
    detail = event['detail']
    logger.info(f"Extracting data from finding ID: {detail.get('id', 'unknown')}")
    
    return {
        'severity': detail['severity'],
        'title': detail['title'],
        'description': detail['description'],
        'finding_type': detail['type'],
        'resource': detail['resource']['resourceType'],
        'account': event['account'],
        'region': event['region'],
        'finding_id': detail['id'],
        'created_at': detail.get('createdAt', ''),
        'updated_at': detail.get('updatedAt', '')
    }


def _send_notifications(config: Dict[str, Any], finding_data: Dict[str, Any]) -> Dict[str, str]:
    """Send notifications via configured channels."""
    results = {}
    
    # SNS Notification
    if _is_enabled('ENABLE_SNS') and os.environ.get('SNS_TOPIC_ARN'):
        logger.info("SNS notification enabled, attempting to send")
        try:
            _send_sns_notification(config, finding_data)
            results['sns'] = 'Success'
            logger.info("SNS notification completed successfully")
        except Exception as e:
            logger.error(f"SNS notification failed: {str(e)}")
            results['sns'] = f'Failed: {str(e)}'
    
    # Email Notification
    if _is_enabled('ENABLE_EMAIL'):
        logger.info("Email notification enabled, attempting to send")
        try:
            _send_email_notification(config, finding_data)
            results['email'] = 'Success'
            logger.info("Email notification completed successfully")
        except Exception as e:
            logger.error(f"Email notification failed: {str(e)}")
            results['email'] = f'Failed: {str(e)}'
    
    # Google Chat Notification
    if _is_enabled('ENABLE_CHAT') and os.environ.get('GOOGLE_CHAT_WEBHOOK'):
        logger.info("Google Chat notification enabled, attempting to send")
        try:
            _send_chat_notification(finding_data)
            results['chat'] = 'Success'
            logger.info("Google Chat notification completed successfully")
        except Exception as e:
            logger.error(f"Chat notification failed: {str(e)}")
            results['chat'] = f'Failed: {str(e)}'
    
    return results


def _send_sns_notification(config: Dict[str, Any], finding_data: Dict[str, Any]) -> None:
    """Send SNS notification."""
    logger.info("Creating AWS session for SNS")
    session = get_aws_session(config['awsCredentials'])
    sns_client = session.client('sns')
    
    logger.info("Formatting SNS message")
    message = _format_sns_message(finding_data)
    subject = f"🚨 GuardDuty Alert | {finding_data['title']}"
    subject = subject[:100]  # SNS subject limit is 100 characters
    logger.info(f"SNS subject: {subject}")
    
    logger.info(f"Publishing to SNS topic: {os.environ['SNS_TOPIC_ARN']}")
    sns_client.publish(
        TopicArn=os.environ['SNS_TOPIC_ARN'],
        Subject=subject,
        Message=message
    )
    
    logger.info("SNS notification sent successfully")


def _send_email_notification(config: Dict[str, Any], finding_data: Dict[str, Any]) -> None:
    """Send email notification."""
    logger.info("Formatting email content")
    email_content = _format_email_content(finding_data)
    
    email_details = config['emailNotification'].copy()
    email_details['email_subject'] = f"GuardDuty Alert | {finding_data['title']}"
    logger.info(f"Email subject: {email_details['email_subject']}")
    logger.info(f"Email recipients: {email_details.get('email_to', [])}")
    
    logger.info("Sending email via SMTP")
    send_email(config['smtpCredentials'], email_details, email_content)
    logger.info("Email notification sent successfully")


def _send_chat_notification(finding_data: Dict[str, Any]) -> None:
    """Send Google Chat notification."""
    logger.info("Formatting Google Chat message")
    message = _format_chat_message(finding_data)
    
    webhook_url = os.environ['GOOGLE_CHAT_WEBHOOK']
    logger.info(f"Posting to Google Chat webhook: {webhook_url[:50]}...")
    response = requests.post(
        webhook_url,
        json=message,
        timeout=10
    )
    
    response.raise_for_status()
    logger.info(f"Google Chat response status: {response.status_code}")
    logger.info("Google Chat notification sent successfully")


def _format_sns_message(finding_data: Dict[str, Any]) -> str:
    """Format message for SNS notification."""
    return f"""GuardDuty Security Alert

Title: {finding_data['title']}
Description: {finding_data['description']}
Type: {finding_data['finding_type']}
Severity: {finding_data['severity']}
Resource: {finding_data['resource']}
Account: {finding_data['account']}
Region: {finding_data['region']}
Finding ID: {finding_data['finding_id']}

Action Required: Please investigate this finding in the AWS GuardDuty console immediately."""


def _format_email_content(finding_data: Dict[str, Any]) -> str:
    """Format HTML content for email notification."""
    severity_color = _get_severity_color(finding_data['severity'])
    
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; margin: 20px;">
        <div style="border-left: 4px solid {severity_color}; padding-left: 20px;">
            <h2 style="color: {severity_color};">🚨 GuardDuty Security Alert</h2>
            
            <table style="border-collapse: collapse; width: 100%; margin-top: 20px;">
                <tr><td style="padding: 8px; font-weight: bold; background-color: #f5f5f5;">Title:</td>
                    <td style="padding: 8px;">{finding_data['title']}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold; background-color: #f5f5f5;">Description:</td>
                    <td style="padding: 8px;">{finding_data['description']}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold; background-color: #f5f5f5;">Type:</td>
                    <td style="padding: 8px;">{finding_data['finding_type']}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold; background-color: #f5f5f5;">Severity:</td>
                    <td style="padding: 8px; color: {severity_color}; font-weight: bold;">{finding_data['severity']}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold; background-color: #f5f5f5;">Resource:</td>
                    <td style="padding: 8px;">{finding_data['resource']}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold; background-color: #f5f5f5;">Account:</td>
                    <td style="padding: 8px;">{finding_data['account']}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold; background-color: #f5f5f5;">Region:</td>
                    <td style="padding: 8px;">{finding_data['region']}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold; background-color: #f5f5f5;">Finding ID:</td>
                    <td style="padding: 8px; font-family: monospace;">{finding_data['finding_id']}</td></tr>
            </table>
            
            <div style="margin-top: 20px; padding: 15px; background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px;">
                <strong>Action Required:</strong> Please investigate this finding in the AWS GuardDuty console immediately.
            </div>
        </div>
    </body>
    </html>
    """


def _format_chat_message(finding_data: Dict[str, Any]) -> Dict[str, str]:
    """Format message for Google Chat notification."""
    return {
        "text": f"""🚨 *GuardDuty Security Alert*

*Title:* {finding_data['title']}
*Description:* {finding_data['description']}
*Type:* {finding_data['finding_type']}
*Severity:* {finding_data['severity']}
*Resource:* {finding_data['resource']}
*Account:* {finding_data['account']}
*Region:* {finding_data['region']}
*Finding ID:* {finding_data['finding_id']}

⚠️ *Action Required:* Please investigate this finding in the AWS GuardDuty console immediately."""
    }


def _get_severity_color(severity: float) -> str:
    """Get color code based on severity level."""
    if severity >= 7.0:
        return "#dc3545"  # Red for high severity
    elif severity >= 4.0:
        return "#fd7e14"  # Orange for medium severity
    else:
        return "#28a745"  # Green for low severity


def _is_enabled(env_var: str) -> bool:
    """Check if notification channel is enabled."""
    return os.environ.get(env_var, 'false').lower() == 'true'