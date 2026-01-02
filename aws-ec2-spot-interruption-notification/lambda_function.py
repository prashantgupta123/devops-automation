"""
AWS EC2 Spot Instance Interruption Notification Handler

This module processes EC2 Spot Instance interruption warnings and sends
multi-channel notifications with ECS service impact analysis.
"""

import json
import os
import logging
import time
from datetime import datetime
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
        Dict containing statusCode and body in AWS Lambda format
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
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "status": "no_services_found", 
                    "instance_id": instance_id
                })
            }
        
        filtered_services = _filter_impacted_services(
            aws_clients['ecs'], 
            instance_info.get('cluster_name'), 
            service_names, 
            instance_id
        )
        
        if not _should_send_alert(instance_info, filtered_services):
            logger.info("Alert suppressed based on business rules")
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "status": "alert_suppressed", 
                    "instance_id": instance_id
                })
            }
        
        # Use filtered services for notifications
        if not filtered_services:
            logger.info("No services will be impacted by interruption")
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "status": "no_impact", 
                    "instance_id": instance_id
                })
            }
        
        _publish_custom_metrics(instance_info, filtered_services, aws_clients['cloudwatch'])
        
        # Send notifications
        notification_results = _send_notifications(
            aws_clients,
            config,
            instance_info,
            filtered_services
        )
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "status": "success",
                "instance_id": instance_id,
                "services_affected": len(filtered_services),
                "notifications_sent": notification_results
            })
        }
        
    except Exception as e:
        logger.error(
            "Failed to process spot interruption event",
            extra={"error": str(e)},
            exc_info=True
        )
        return {
            "statusCode": 500,
            "body": json.dumps({
                "status": "error", 
                "message": str(e)
            })
        }


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
        'sns': session.client('sns'),
        'cloudwatch': session.client('cloudwatch')
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
    message = _format_notification_message(instance_info, service_names, config)
    notifications_sent = []
    
    # SNS Notification
    if os.environ.get('ENABLE_SNS', 'false').lower() == 'true':
        if _send_sns_notification(aws_clients['sns'], message, config):
            notifications_sent.append('SNS')
    
    # Google Chat Notification
    if os.environ.get('ENABLE_CHAT', 'false').lower() == 'true':
        if _send_chat_notification(message):
            notifications_sent.append('Google Chat')
    
    # Email Notification
    if os.environ.get('ENABLE_EMAIL', 'false').lower() == 'true':
        if _send_email_notification(config, message):
            notifications_sent.append('Email')
    
    # Slack Notification
    if os.environ.get('ENABLE_SLACK', 'false').lower() == 'true':
        if _send_slack_notification(instance_info, service_names, config):
            notifications_sent.append('Slack')
    
    # JIRA Integration
    if os.environ.get('ENABLE_JIRA', 'false').lower() == 'true':
        if _is_critical_interruption(service_names):
            _create_jira_ticket(instance_info, service_names)
            notifications_sent.append('JIRA')
    
    return notifications_sent


def _format_notification_message(
    instance_info: Dict[str, Any], 
    service_names: List[str],
    config: Dict[str, Any]
) -> str:
    """Format notification message with instance and service details."""
    services_text = '\n'.join(f"• {service}" for service in service_names)
    subject = config.get('emailNotification', {}).get('email_subject', 'EC2 Spot Instance Interruption Alert')
    
    return f"""🚨 **{subject}**

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


def _send_sns_notification(sns_client, message: str, config: Dict[str, Any]) -> bool:
    """Send notification via SNS."""
    try:
        subject = config.get('emailNotification', {}).get('email_subject', 'EC2 Spot Instance Interruption Alert')
        sns_client.publish(
            TopicArn=os.environ['SNS_TOPIC_ARN'],
            Subject=subject,
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


def _should_send_alert(instance_info: Dict[str, Any], service_names: List[str]) -> bool:
    """Determine if alert should be sent based on business rules."""
    
    # Skip alerts during maintenance windows
    if _is_maintenance_window():
        logger.info("Skipping alert during maintenance window")
        return False
    
    # Skip alerts for non-critical services
    critical_services = os.environ.get('CRITICAL_SERVICES', '').split(',')
    if critical_services and not any(
        service in critical_services for service in service_names
    ):
        logger.info("No critical services affected, skipping alert")
        return False
    
    return True


def _is_maintenance_window() -> bool:
    """Check if current time is within maintenance window."""
    maintenance_start = os.environ.get('MAINTENANCE_START')
    maintenance_end = os.environ.get('MAINTENANCE_END')
    
    # Skip check if maintenance window not defined
    if not maintenance_start or not maintenance_end:
        return False
    
    try:
        current_time = datetime.now().time()
        start_time = datetime.strptime(maintenance_start, '%H:%M').time()
        end_time = datetime.strptime(maintenance_end, '%H:%M').time()
        
        return start_time <= current_time <= end_time
    except Exception:
        return False


def _filter_impacted_services(
    ecs_client,
    cluster_name: str,
    service_names: List[str],
    interrupted_instance_id: str
) -> List[str]:
    """Filter services that will be impacted by spot interruption."""
    impacted_services = []
    
    for service_name in service_names:
        try:
            # Get service details
            service_details = ecs_client.describe_services(
                cluster=cluster_name,
                services=[service_name]
            )
            
            if not service_details or not service_details['services']:
                impacted_services.append(service_name)
                continue
                
            # Check if all running tasks are on the interrupted instance
            tasks = ecs_client.list_tasks(
                cluster=cluster_name,
                serviceName=service_name
            )
            
            tasks_on_other_instances = 0
            for task_arn in tasks.get('taskArns', []):
                task_details = ecs_client.describe_tasks(
                    cluster=cluster_name,
                    tasks=[task_arn]
                )
                
                if task_details and task_details['tasks']:
                    # Get container instance for this task
                    container_instance_arn = task_details['tasks'][0].get('containerInstanceArn')
                    if container_instance_arn:
                        instance_details = ecs_client.describe_container_instances(
                            cluster=cluster_name,
                            containerInstances=[container_instance_arn]
                        )
                        
                        if (instance_details and instance_details['containerInstances'] and
                            instance_details['containerInstances'][0]['ec2InstanceId'] != interrupted_instance_id):
                            tasks_on_other_instances += 1
            
            # If service has tasks running on other instances, it won't be impacted
            if tasks_on_other_instances == 0:
                impacted_services.append(service_name)
                
        except Exception as e:
            logger.error(f"Failed to check service impact for {service_name}: {e}")
            # Include service in alert if we can't determine impact
            impacted_services.append(service_name)
    
    return impacted_services


def _publish_custom_metrics(
    instance_info: Dict[str, Any], 
    service_names: List[str], 
    cloudwatch_client
) -> None:
    """Publish custom CloudWatch metrics."""
    try:
        # Metric: Spot interruptions by instance type
        cloudwatch_client.put_metric_data(
            Namespace='SpotInterruption',
            MetricData=[
                {
                    'MetricName': 'InterruptionCount',
                    'Dimensions': [
                        {
                            'Name': 'InstanceType',
                            'Value': instance_info.get('instance_type', 'Unknown')
                        }
                    ],
                    'Value': 1,
                    'Unit': 'Count'
                }
            ]
        )
        
        logger.info("Custom metrics published successfully")
        
    except Exception as e:
        logger.error(f"Failed to publish metrics: {e}")


def _send_slack_notification(
    instance_info: Dict[str, Any], 
    service_names: List[str],
    config: Dict[str, Any]
) -> bool:
    """Send notification to Slack via webhook."""
    webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    if not webhook_url:
        return False
    
    subject = config.get('emailNotification', {}).get('email_subject', 'EC2 Spot Instance Interruption Alert')
    slack_message = {
        "text": subject,
        "attachments": [
            {
                "color": "danger",
                "text": f"Instance {instance_info.get('instance_id')} will be interrupted. Services: {', '.join(service_names)}",
                "footer": "AWS Lambda Alert System",
                "ts": int(time.time())
            }
        ]
    }
    
    try:
        response = requests.post(webhook_url, json=slack_message, timeout=10)
        response.raise_for_status()
        logger.info("Slack notification sent successfully")
        return True
    except Exception as e:
        logger.error(f"Slack notification failed: {e}")
        return False


def _create_jira_ticket(
    instance_info: Dict[str, Any], 
    service_names: List[str]
) -> None:
    """Create JIRA ticket for critical service interruptions."""
    jira_url = os.environ.get('JIRA_URL')
    jira_username = os.environ.get('JIRA_USERNAME')
    jira_token = os.environ.get('JIRA_TOKEN')
    
    if not all([jira_url, jira_username, jira_token]):
        logger.warning("JIRA credentials not configured")
        return
    
    ticket_data = {
        'fields': {
            'project': {'key': os.environ.get('JIRA_PROJECT', 'INFRA')},
            'summary': f"Spot Instance Interruption: {instance_info.get('instance_id')}",
            'description': f"Services affected: {', '.join(service_names)}",
            'issuetype': {'name': 'Incident'},
            'priority': {'name': 'High'}
        }
    }
    
    try:
        response = requests.post(
            f"{jira_url}/rest/api/2/issue",
            json=ticket_data,
            auth=(jira_username, jira_token),
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        response.raise_for_status()
        logger.info("JIRA ticket created successfully")
    except Exception as e:
        logger.error(f"JIRA ticket creation failed: {e}")


def _is_critical_interruption(service_names: List[str]) -> bool:
    """Check if interruption affects critical services."""
    critical_services = os.environ.get('CRITICAL_SERVICES', '').split(',')
    return any(service in critical_services for service in service_names)