"""
AWS ECS Service Monitoring Lambda Function

This Lambda function monitors AWS ECS service events and sends notifications
when critical issues occur. It processes CloudWatch Events for ECS services
and publishes alerts via SNS while creating custom CloudWatch metrics.

Author: Prashant Gupta
"""

import json
import logging
import os
from typing import Any, Dict, Optional, Tuple

import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment configuration
REQUIRED_ENV_VARS = ['REGION', 'ALERT_TOPIC_ARN', 'PROJECT_NAME', 'ENV']
REGION = os.environ.get('REGION')
ALERT_TOPIC_ARN = os.environ.get('ALERT_TOPIC_ARN')
PROJECT_NAME = os.environ.get('PROJECT_NAME')
ENV = os.environ.get('ENV')

# Constants
CUSTOM_METRIC_NAME = 'ECSServiceErrorEventsCount'
CLOUDWATCH_NAMESPACE = 'AWS/ECS'

# Event type mappings
EVENT_MAPPINGS = {
    'SERVICE_TASK_PLACEMENT_FAILURE': (
        'ECS Service Task Placement Failure',
        'Not enough CPU or memory capacity on the available container instances or no container instances being available'
    ),
    'SERVICE_TASK_CONFIGURATION_FAILURE': (
        'ECS Service Task Configuration Failure',
        'Tags were being applied to the service but the user or role had not opted in to the new Amazon Resource Name (ARN) format in the Region'
    ),
    'SERVICE_DAEMON_PLACEMENT_CONSTRAINT_VIOLATED': (
        'ECS Service Daemon Placement Constraint Violated',
        'A task in a service using the DAEMON service scheduler strategy no longer meets the placement constraint strategy for the service'
    ),
    'ECS_OPERATION_THROTTLED': (
        'ECS Operation Throttled',
        'The service scheduler has been throttled due to the Amazon ECS API throttle limits'
    ),
    'SERVICE_DISCOVERY_OPERATION_THROTTLED': (
        'ECS Service Discovery Operation Throttled',
        'The service scheduler has been throttled due to the AWS Cloud Map API throttle limits. This can occur on services configured to use service discovery'
    ),
    'SERVICE_DEPLOYMENT_FAILED': (
        'ECS Service Deployment Failed',
        'A service deployment did not reach steady state. This happens when a CloudWatch alarm is triggered or the circuit breaker detects a service deployment failure'
    ),
    'SERVICE_TASK_START_IMPAIRED': (
        'ECS Service Task Start Impaired',
        'The service is unable to consistently start tasks successfully'
    ),
    'SERVICE_DISCOVERY_INSTANCE_UNHEALTHY': (
        'ECS Service Discovery Instance Unhealthy',
        'A service using service discovery contains an unhealthy task. The service scheduler detects that a task within a service registry is unhealthy'
    ),
    'VPC_LATTICE_TARGET_UNHEALTHY': (
        'ECS Service VPC Lattice Target Unhealthy',
        'The service using VPC Lattice has detected one of the targets for the VPC Lattice is unhealthy'
    )
}


def validate_environment() -> None:
    """Validate that all required environment variables are set."""
    missing_vars = [var for var in REQUIRED_ENV_VARS if not os.environ.get(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")


def publish_cloudwatch_metric(
    cluster_name: str,
    service_name: str,
    metric_name: str,
    count_value: float
) -> None:
    """
    Publish custom metric data to CloudWatch.

    Args:
        cluster_name: Name of the ECS cluster
        service_name: Name of the ECS service
        metric_name: Name of the custom metric
        count_value: Metric value to publish
    """
    try:
        cloudwatch_client = boto3.client('cloudwatch', region_name=REGION)
        cloudwatch_client.put_metric_data(
            Namespace=CLOUDWATCH_NAMESPACE,
            MetricData=[
                {
                    'MetricName': metric_name,
                    'Dimensions': [
                        {'Name': 'ClusterName', 'Value': cluster_name},
                        {'Name': 'ServiceName', 'Value': service_name}
                    ],
                    'Value': count_value,
                    'Unit': 'Count'
                }
            ]
        )
        logger.info(f"Published metric {metric_name} for {cluster_name}/{service_name}")
    except ClientError as e:
        logger.error(f"Failed to publish CloudWatch metric: {e}")
        raise


def send_sns_notification(subject: str, message: str) -> None:
    """
    Send notification via SNS topic.

    Args:
        subject: Email subject line
        message: Email message body
    """
    try:
        sns_client = boto3.client('sns', region_name=REGION)
        logger.info(f"Sending SNS notification - Subject: {subject}")
        logger.debug(f"SNS Message: {message}")
        
        sns_client.publish(
            TopicArn=ALERT_TOPIC_ARN,
            Subject=subject[:100],  # SNS subject limit is 100 characters
            Message=message
        )
        logger.info("SNS notification sent successfully")
    except ClientError as e:
        logger.error(f"Failed to send SNS notification: {e}")
        raise


def parse_ecs_event(event: Dict[str, Any]) -> Tuple[str, str, str, str, str, str]:
    """
    Parse ECS CloudWatch event and extract relevant information.

    Args:
        event: CloudWatch event dictionary

    Returns:
        Tuple containing (region, cluster_name, service_name, event_name, event_type, reason)
    """
    region = event.get('region', 'unknown')
    
    # Extract cluster and service names from resource ARN
    resource_arn = event.get('resources', [''])[0]
    arn_parts = resource_arn.split('/', 2)
    cluster_name = arn_parts[1] if len(arn_parts) > 1 else 'unknown'
    service_name = arn_parts[2] if len(arn_parts) > 2 else 'unknown'
    
    detail = event.get('detail', {})
    event_name = detail.get('eventName', 'UNKNOWN_EVENT')
    event_type = detail.get('eventType', 'UNKNOWN')
    reason = detail.get('reason', '')
    
    return region, cluster_name, service_name, event_name, event_type, reason


def get_event_details(event_name: str) -> Optional[Tuple[str, str]]:
    """
    Get subject and message body for a given event name.

    Args:
        event_name: Name of the ECS event

    Returns:
        Tuple of (subject, message_body) or None if event not mapped
    """
    return EVENT_MAPPINGS.get(event_name)


def format_notification(
    cluster_name: str,
    service_name: str,
    region: str,
    event_name: str,
    reason: str,
    subject: str,
    message_body: str
) -> Tuple[str, str]:
    """
    Format SNS notification subject and message.

    Args:
        cluster_name: ECS cluster name
        service_name: ECS service name
        region: AWS region
        event_name: Event name
        reason: Event reason (if available)
        subject: Base subject line
        message_body: Base message body

    Returns:
        Tuple of (formatted_subject, formatted_message)
    """
    formatted_subject = f"{PROJECT_NAME} | {ENV} | ERROR: {subject}"
    formatted_message = (
        f"Hi,\n\n"
        f"Cluster Name: {cluster_name}\n"
        f"Service Name: {service_name}\n"
        f"Region: {region}\n"
        f"Event Name: {event_name}\n"
        f"Reason: {reason}\n"
        f"Message: {message_body}"
    )
    return formatted_subject, formatted_message


def process_ecs_event(event: Dict[str, Any]) -> None:
    """
    Process ECS CloudWatch event and send notifications if needed.

    Args:
        event: CloudWatch event dictionary
    """
    # Parse event details
    region, cluster_name, service_name, event_name, event_type, reason = parse_ecs_event(event)
    
    logger.info(
        f"Processing event: {event_name} for {cluster_name}/{service_name} "
        f"(type: {event_type})"
    )
    
    # Check if this is a monitored event
    event_details = get_event_details(event_name)
    
    if event_details:
        subject, message_body = event_details
        formatted_subject, formatted_message = format_notification(
            cluster_name, service_name, region, event_name, reason, subject, message_body
        )
        
        # Send notification and publish metric
        send_sns_notification(formatted_subject, formatted_message)
        publish_cloudwatch_metric(cluster_name, service_name, CUSTOM_METRIC_NAME, 1.0)
        
    elif event_type == 'ERROR':
        # Handle unmapped error events
        logger.warning(f"Unmapped ERROR event type: {event_name}")
        subject = f"{PROJECT_NAME} | {ENV} | ERROR: ECS Error Service Events"
        message = f"Hi,\n\nUnmapped error event detected:\n{json.dumps(event, indent=2)}"
        send_sns_notification(subject, message)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function handler for ECS service monitoring.

    Args:
        event: CloudWatch event data
        context: Lambda context object

    Returns:
        Response dictionary with status code and message
    """
    try:
        # Validate environment on cold start
        validate_environment()
        
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Validate event source
        if event.get('source') != 'aws.ecs':
            logger.warning(f"Unsupported event source: {event.get('source')}")
            return {
                'statusCode': 400,
                'body': json.dumps('Function only supports events from aws.ecs source')
            }
        
        # Process the ECS event
        process_ecs_event(event)
        
        return {
            'statusCode': 200,
            'body': json.dumps('Event processed successfully')
        }
        
    except Exception as e:
        logger.error(f"Error processing event: {str(e)}", exc_info=True)
        
        # Send error notification
        try:
            subject = f"{PROJECT_NAME} | {ENV} | ERROR: ECS Service Events Processing Failed"
            message = (
                f"Hi,\n\n"
                f"An error occurred while processing ECS event:\n\n"
                f"Error: {str(e)}\n\n"
                f"Event: {json.dumps(event, indent=2)}"
            )
            send_sns_notification(subject, message)
        except Exception as notification_error:
            logger.error(f"Failed to send error notification: {notification_error}")
        
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error processing event: {str(e)}')
        }
