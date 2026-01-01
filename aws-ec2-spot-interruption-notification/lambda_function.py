"""
AWS EC2 Spot Instance Interruption Notification Handler

This module processes EC2 Spot Instance interruption warnings and sends
multi-channel notifications with ECS service impact analysis.
"""

import json
import os
import logging
from typing import Dict, List, Any, Optional
import requests
from AWSSession import get_aws_session
from Notification import send_email

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for processing EC2 Spot Instance interruption warnings.
    
    Args:
        event: EventBridge event containing interruption details
        context: Lambda runtime context
        
    Returns:
        Dict containing processing status and notification results
    """
    logger.info("Processing spot interruption event", extra={"event": event})
    
    try:
        instance_id = _extract_instance_id(event)
        config = _load_configuration()
        
        # Initialize AWS clients
        session = get_aws_session(config['awsCredentials'])
        aws_clients = _initialize_aws_clients(session)
        
        # Analyze instance and discover services
        instance_info = _analyze_instance(aws_clients['ec2'], instance_id)
        service_names = _discover_ecs_services(
            aws_clients['ecs'], 
            instance_id, 
            instance_info.get('cluster_name')
        )
        
        if not service_names:
            logger.warning(
                "No services found on interrupted instance",
                extra={"instance_id": instance_id}
            )
            return {"status": "no_services_found", "instance_id": instance_id}
        
        # Send notifications
        notification_results = _send_notifications(
            aws_clients,
            config,
            instance_info,
            service_names
        )
        
        return {
            "status": "success",
            "instance_id": instance_id,
            "services_affected": len(service_names),
            "notifications_sent": notification_results
        }
        
    except Exception as e:
        logger.error(
            "Failed to process spot interruption event",
            extra={"error": str(e)},
            exc_info=True
        )
        return {"status": "error", "message": str(e)}


def _extract_instance_id(event: Dict[str, Any]) -> str:
    """Extract instance ID from EventBridge event."""
    return event.get("detail", {}).get("instance-id", "Unknown")


def _load_configuration() -> Dict[str, Any]:
    """Load configuration from input.json file."""
    try:
        with open('input.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise


def _initialize_aws_clients(session) -> Dict[str, Any]:
    """Initialize AWS service clients."""
    return {
        'ec2': session.client('ec2'),
        'ecs': session.client('ecs'),
        'sns': session.client('sns')
    }


def _analyze_instance(ec2_client, instance_id: str) -> Dict[str, Any]:
    """
    Analyze EC2 instance and extract relevant information.
    
    Returns:
        Dict containing instance type, cluster name, and other metadata
    """
    try:
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        
        # Extract cluster name from tags
        cluster_name = None
        for tag in instance.get('Tags', []):
            if tag['Key'] == 'aws:autoscaling:groupName':
                cluster_name = tag['Value']
                break
        
        return {
            'instance_id': instance_id,
            'instance_type': instance.get('InstanceType', 'Unknown'),
            'cluster_name': cluster_name,
            'availability_zone': instance.get('Placement', {}).get('AvailabilityZone')
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze instance {instance_id}: {e}")
        raise


def _discover_ecs_services(
    ecs_client, 
    instance_id: str, 
    cluster_name: Optional[str]
) -> List[str]:
    """
    Discover ECS services running on the interrupted instance.
    
    Returns:
        List of service names (excluding daemon services)
    """
    if not cluster_name:
        return []
    
    service_names = []
    
    try:
        # Find container instances in the cluster
        container_instances = ecs_client.list_container_instances(
            cluster=cluster_name
        )
        
        for arn in container_instances.get('containerInstanceArns', []):
            if _is_target_instance(ecs_client, cluster_name, arn, instance_id):
                services = _get_services_on_instance(
                    ecs_client, 
                    cluster_name, 
                    arn
                )
                service_names.extend(services)
        
        return list(set(service_names))  # Remove duplicates
        
    except Exception as e:
        logger.error(
            f"Failed to discover ECS services for instance {instance_id}: {e}"
        )
        return []


def _is_target_instance(
    ecs_client, 
    cluster_name: str, 
    container_instance_arn: str, 
    target_instance_id: str
) -> bool:
    """Check if container instance matches target EC2 instance."""
    try:
        details = ecs_client.describe_container_instances(
            cluster=cluster_name,
            containerInstances=[container_instance_arn]
        )
        
        if details and details['containerInstances']:
            return details['containerInstances'][0]['ec2InstanceId'] == target_instance_id
            
    except Exception as e:
        logger.error(f"Failed to check container instance: {e}")
    
    return False


def _get_services_on_instance(
    ecs_client, 
    cluster_name: str, 
    container_instance_arn: str
) -> List[str]:
    """Get non-daemon services running on a container instance."""
    services = []
    
    try:
        # Get tasks on the container instance
        tasks = ecs_client.list_tasks(
            cluster=cluster_name,
            containerInstance=container_instance_arn
        )
        
        for task_arn in tasks.get('taskArns', []):
            service_name = _extract_service_from_task(
                ecs_client, 
                cluster_name, 
                task_arn
            )
            if service_name:
                services.append(service_name)
        
        return services
        
    except Exception as e:
        logger.error(f"Failed to get services on instance: {e}")
        return []


def _extract_service_from_task(
    ecs_client, 
    cluster_name: str, 
    task_arn: str
) -> Optional[str]:
    """Extract service name from task, filtering out daemon services."""
    try:
        task_details = ecs_client.describe_tasks(
            cluster=cluster_name,
            tasks=[task_arn]
        )
        
        if not task_details or not task_details['tasks']:
            return None
            
        task = task_details['tasks'][0]
        service_name = task.get('group', '')
        
        if not service_name.startswith('service:'):
            return None
            
        service_name_cleaned = service_name.split(':', 1)[1]
        
        # Check if it's a daemon service
        if _is_daemon_service(ecs_client, cluster_name, service_name_cleaned):
            return None
            
        return service_name_cleaned
        
    except Exception as e:
        logger.error(f"Failed to extract service from task: {e}")
        return None


def _is_daemon_service(
    ecs_client, 
    cluster_name: str, 
    service_name: str
) -> bool:
    """Check if service is a daemon service."""
    try:
        service_details = ecs_client.describe_services(
            cluster=cluster_name,
            services=[service_name]
        )
        
        if service_details and service_details['services']:
            service = service_details['services'][0]
            return service.get('schedulingStrategy') == 'DAEMON'
            
    except Exception as e:
        logger.error(f"Failed to check service type: {e}")
    
    return False


def _send_notifications(
    aws_clients: Dict[str, Any],
    config: Dict[str, Any],
    instance_info: Dict[str, Any],
    service_names: List[str]
) -> List[str]:
    """Send notifications via enabled channels."""
    message = _format_notification_message(instance_info, service_names)
    notifications_sent = []
    
    # SNS Notification
    if os.environ.get('ENABLE_SNS', 'false').lower() == 'true':
        if _send_sns_notification(aws_clients['sns'], message):
            notifications_sent.append('SNS')
    
    # Google Chat Notification
    if os.environ.get('ENABLE_CHAT', 'false').lower() == 'true':
        if _send_chat_notification(message):
            notifications_sent.append('Google Chat')
    
    # Email Notification
    if os.environ.get('ENABLE_EMAIL', 'false').lower() == 'true':
        if _send_email_notification(config, message):
            notifications_sent.append('Email')
    
    return notifications_sent


def _format_notification_message(
    instance_info: Dict[str, Any], 
    service_names: List[str]
) -> str:
    """Format notification message with instance and service details."""
    services_text = '\n'.join(f"• {service}" for service in service_names)
    
    return f"""🚨 **EC2 Spot Instance Interruption Alert**

**Instance Details:**
• Instance ID: {instance_info.get('instance_id', 'Unknown')}
• Instance Type: {instance_info.get('instance_type', 'Unknown')}
• Availability Zone: {instance_info.get('availability_zone', 'Unknown')}

**Affected Services:**
{services_text}

**Action Required:**
This instance will be interrupted in approximately 2 minutes. 
Services will experience brief downtime during failover.

**Next Steps:**
1. Monitor service health dashboards
2. Verify auto-scaling group capacity
3. Check for any stuck deployments

---
*Automated alert from AWS Lambda*"""


def _send_sns_notification(sns_client, message: str) -> bool:
    """Send notification via SNS."""
    try:
        sns_client.publish(
            TopicArn=os.environ['SNS_TOPIC_ARN'],
            Subject="🚨 EC2 Spot Instance Interruption Alert",
            Message=message
        )
        logger.info("SNS notification sent successfully")
        return True
    except Exception as e:
        logger.error(f"SNS notification failed: {e}")
        return False


def _send_chat_notification(message: str) -> bool:
    """Send notification via Google Chat webhook."""
    try:
        webhook_url = os.environ['GOOGLE_CHAT_WEBHOOK']
        response = requests.post(
            webhook_url,
            json={"text": message},
            timeout=10
        )
        response.raise_for_status()
        logger.info("Google Chat notification sent successfully")
        return True
    except Exception as e:
        logger.error(f"Google Chat notification failed: {e}")
        return False


def _send_email_notification(config: Dict[str, Any], message: str) -> bool:
    """Send notification via SMTP email."""
    try:
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <pre style="background-color: #f4f4f4; padding: 20px; border-radius: 5px;">
{message}
            </pre>
        </body>
        </html>
        """
        
        send_email(
            config['smtpCredentials'],
            config['emailNotification'],
            html_content
        )
        logger.info("Email notification sent successfully")
        return True
    except Exception as e:
        logger.error(f"Email notification failed: {e}")
        return False
