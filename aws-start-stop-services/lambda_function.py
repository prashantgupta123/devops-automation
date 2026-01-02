"""
AWS EC2 Start/Stop Lambda Function

This Lambda function provides automated start and stop capabilities for EC2 instances
based on EventBridge scheduled events. It supports multi-instance operations with
SNS notifications for success and failure scenarios.

Author: DevOps Team
Version: 2.0.0
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError, BotoCoreError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
REGION_NAME: str = os.getenv('AWS_REGION_NAME', 'ap-south-1')
SNS_TOPIC_ARN: str = os.getenv('SNS_TOPIC_ARN', '')
SNS_SUBJECT_PREFIX: str = os.getenv('SNS_SUBJECT_PREFIX', 'Service Notification')

# AWS clients
ec2_client = boto3.client('ec2', region_name=REGION_NAME)
sns_client = boto3.client('sns', region_name=REGION_NAME)


class EC2InstanceManager:
    """Manages EC2 instance start and stop operations."""

    def __init__(self, ec2_client, sns_client):
        """
        Initialize EC2 Instance Manager.

        Args:
            ec2_client: Boto3 EC2 client instance
            sns_client: Boto3 SNS client instance
        """
        self.ec2 = ec2_client
        self.sns = sns_client

    def start_instances(self, instance_ids: List[str]) -> Dict[str, Any]:
        """
        Start EC2 instances.

        Args:
            instance_ids: List of EC2 instance IDs to start

        Returns:
            Dict containing the EC2 API response

        Raises:
            ClientError: If AWS API call fails
        """
        logger.info(f"Starting instances: {instance_ids}")
        return self.ec2.start_instances(InstanceIds=instance_ids)

    def stop_instances(self, instance_ids: List[str]) -> Dict[str, Any]:
        """
        Stop EC2 instances.

        Args:
            instance_ids: List of EC2 instance IDs to stop

        Returns:
            Dict containing the EC2 API response

        Raises:
            ClientError: If AWS API call fails
        """
        logger.info(f"Stopping instances: {instance_ids}")
        return self.ec2.stop_instances(InstanceIds=instance_ids)


class NotificationService:
    """Handles SNS notification publishing."""

    def __init__(self, sns_client, topic_arn: str, subject_prefix: str):
        """
        Initialize Notification Service.

        Args:
            sns_client: Boto3 SNS client instance
            topic_arn: SNS topic ARN for notifications
            subject_prefix: Prefix for notification subjects
        """
        self.sns = sns_client
        self.topic_arn = topic_arn
        self.subject_prefix = subject_prefix

    def send_notification(
        self,
        action: str,
        module: str,
        instance_details: Dict[str, str],
        status: str = "INFO",
        error_message: Optional[str] = None
    ) -> None:
        """
        Send SNS notification.

        Args:
            action: Action performed (start/stop)
            module: Module name
            instance_details: Dictionary of instance IDs and names
            status: Notification status (INFO/ERROR)
            error_message: Optional error message for failures
        """
        if not self.topic_arn:
            logger.warning("SNS topic ARN not configured. Skipping notification.")
            return

        subject = f"{self.subject_prefix} | {status} | {action.upper()} - {module}"
        
        if error_message:
            message = (
                f"Error: {error_message}\n\n"
                f"Module: {module}\n"
                f"Action: {action}\n"
                f"Instances: {list(instance_details.keys())}"
            )
        else:
            message = (
                f"Hi,\n\n"
                f"Successfully {action}ed instances for module '{module}'\n\n"
                f"Instance Details:\n{json.dumps(instance_details, indent=2)}"
            )

        try:
            self.sns.publish(
                TopicArn=self.topic_arn,
                Subject=subject,
                Message=message
            )
            logger.info(f"Notification sent: {subject}")
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to send SNS notification: {str(e)}")


def validate_event(event: Dict[str, Any]) -> tuple[str, str, Dict[str, str]]:
    """
    Validate and extract required parameters from event.

    Args:
        event: Lambda event dictionary

    Returns:
        Tuple of (action, module, instance_details)

    Raises:
        ValueError: If required parameters are missing or invalid
    """
    action = event.get('action')
    module = event.get('module')
    instance_details = event.get('instance_details', {})

    if not action:
        raise ValueError("Missing required parameter: 'action'")
    
    if action not in ['start', 'stop']:
        raise ValueError(f"Invalid action: '{action}'. Must be 'start' or 'stop'")
    
    if not module:
        raise ValueError("Missing required parameter: 'module'")
    
    if not instance_details or not isinstance(instance_details, dict):
        raise ValueError("Missing or invalid 'instance_details'. Must be a non-empty dictionary")

    return action, module, instance_details


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler function for EC2 start/stop operations.

    Args:
        event: Lambda event containing action, module, and instance_details
        context: Lambda context object

    Returns:
        Dict containing statusCode and response body

    Event Structure:
        {
            "action": "start" | "stop",
            "module": "module-name",
            "instance_details": {
                "i-xxxxx": "instance-name",
                ...
            }
        }
    """
    logger.info(f"Received event: {json.dumps(event)}")

    # Initialize services
    instance_manager = EC2InstanceManager(ec2_client, sns_client)
    notification_service = NotificationService(
        sns_client, SNS_TOPIC_ARN, SNS_SUBJECT_PREFIX
    )

    try:
        # Validate event
        action, module, instance_details = validate_event(event)
        instance_ids = list(instance_details.keys())

        # Perform action
        if action == 'start':
            response = instance_manager.start_instances(instance_ids)
            message = f"Successfully started instances for module '{module}'"
        else:  # action == 'stop'
            response = instance_manager.stop_instances(instance_ids)
            message = f"Successfully stopped instances for module '{module}'"

        logger.info(message)

        # Send success notification
        notification_service.send_notification(
            action=action,
            module=module,
            instance_details=instance_details,
            status="INFO"
        )

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': message,
                'instance_ids': instance_ids,
                'response': response
            })
        }

    except ValueError as e:
        error_msg = f"Validation error: {str(e)}"
        logger.error(error_msg)
        return {
            'statusCode': 400,
            'body': json.dumps({'error': error_msg})
        }

    except (ClientError, BotoCoreError) as e:
        error_msg = f"AWS API error: {str(e)}"
        logger.error(error_msg, exc_info=True)

        # Send failure notification
        notification_service.send_notification(
            action=event.get('action', 'unknown'),
            module=event.get('module', 'unknown'),
            instance_details=event.get('instance_details', {}),
            status="ERROR",
            error_message=str(e)
        )

        return {
            'statusCode': 500,
            'body': json.dumps({'error': error_msg})
        }

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg, exc_info=True)

        # Send failure notification
        notification_service.send_notification(
            action=event.get('action', 'unknown'),
            module=event.get('module', 'unknown'),
            instance_details=event.get('instance_details', {}),
            status="ERROR",
            error_message=str(e)
        )

        return {
            'statusCode': 500,
            'body': json.dumps({'error': error_msg})
        }
