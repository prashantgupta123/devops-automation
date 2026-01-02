"""AWS ECS Service Task Recycle Lambda Function.

Recycles ECS service tasks one by one to avoid parallel replacement.
Maintains service availability during task recycling process.
"""

import json
import time
import logging
from datetime import datetime
from AWSSession import get_aws_session
from Notification import send_email

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """Main Lambda handler for ECS task recycling."""
    try:
        # Load configuration
        with open('input.json', 'r') as f:
            config = json.load(f)
        
        # Extract event parameters
        cluster_name = event['cluster_name']
        service_name = event['service_name']
        maintain_service_state = event.get('maintain_service_state', True)
        wait_time = int(event.get('wait_time', 30))
        
        logger.info(f"Starting task recycle for {cluster_name}/{service_name}")
        
        # Create AWS session and clients
        session = get_aws_session(config['awsCredentials'])
        ecs_client = session.client('ecs')
        asg_client = session.client('application-autoscaling')
        
        # Execute recycling process
        result = recycle_tasks(ecs_client, asg_client, cluster_name, service_name, 
                              maintain_service_state, wait_time)
        
        # Send notification if configured
        if config.get('smtpCredentials') and config.get('emailNotification'):
            send_notification(config, cluster_name, service_name, result)
        
        logger.info("Task recycle completed successfully")
        return {'statusCode': 200, 'body': json.dumps(result)}
        
    except Exception as e:
        logger.error(f"Task recycle failed: {str(e)}")
        raise


def recycle_tasks(ecs_client, asg_client, cluster_name, service_name, 
                 maintain_service_state, wait_time):
    """Execute ECS task recycling process."""
    # Get current service configuration
    service_config = ecs_client.describe_services(
        cluster=cluster_name, services=[service_name]
    )['services'][0]
    
    old_desired_count = service_config['desiredCount']
    old_tasks = ecs_client.list_tasks(
        cluster=cluster_name, serviceName=service_name, desiredStatus='RUNNING'
    )['taskArns']
    
    logger.info(f"Original desired count: {old_desired_count}, tasks: {len(old_tasks)}")
    
    # Get autoscaling configuration
    asg_config = get_autoscaling_config(asg_client, cluster_name, service_name)
    old_min = asg_config['MinCapacity'] if asg_config else None
    old_max = asg_config['MaxCapacity'] if asg_config else None
    
    # Increase capacity if maintaining service state
    if maintain_service_state:
        temp_desired = old_desired_count + 1
        update_service_capacity(ecs_client, cluster_name, service_name, temp_desired)
        
        if asg_config:
            update_autoscaling(asg_client, cluster_name, service_name, 
                             temp_desired, old_max + 1)
        
        wait_for_stable(ecs_client, cluster_name, service_name)
        logger.info(f"Increased capacity to {temp_desired}")
    
    # Recycle tasks one by one
    for i, task_arn in enumerate(old_tasks, 1):
        logger.info(f"Recycling task {i}/{len(old_tasks)}: {task_arn}")
        
        ecs_client.stop_task(
            cluster=cluster_name, task=task_arn, reason='Task recycling process'
        )
        
        wait_for_stable(ecs_client, cluster_name, service_name)
        logger.info(f"Task {i} recycled, waiting {wait_time}s")
        time.sleep(wait_time)
    
    # Restore original capacity
    if maintain_service_state:
        update_service_capacity(ecs_client, cluster_name, service_name, old_desired_count)
        
        if asg_config:
            update_autoscaling(asg_client, cluster_name, service_name, old_min, old_max)
        
        wait_for_stable(ecs_client, cluster_name, service_name)
        logger.info(f"Restored capacity to {old_desired_count}")
    
    return {
        'cluster': cluster_name,
        'service': service_name,
        'tasks_recycled': len(old_tasks),
        'timestamp': datetime.now().isoformat()
    }


def get_autoscaling_config(asg_client, cluster_name, service_name):
    """Get service autoscaling configuration."""
    response = asg_client.describe_scalable_targets(
        ServiceNamespace='ecs',
        ResourceIds=[f"service/{cluster_name}/{service_name}"],
        ScalableDimension='ecs:service:DesiredCount'
    )
    return response['ScalableTargets'][0] if response.get('ScalableTargets') else None


def update_service_capacity(ecs_client, cluster_name, service_name, desired_count):
    """Update ECS service desired count."""
    ecs_client.update_service(
        cluster=cluster_name, service=service_name, desiredCount=desired_count
    )


def update_autoscaling(asg_client, cluster_name, service_name, min_capacity, max_capacity):
    """Update service autoscaling configuration."""
    asg_client.register_scalable_target(
        ServiceNamespace='ecs',
        ResourceId=f"service/{cluster_name}/{service_name}",
        ScalableDimension='ecs:service:DesiredCount',
        MinCapacity=min_capacity,
        MaxCapacity=max_capacity
    )


def wait_for_stable(ecs_client, cluster_name, service_name):
    """Wait for service to reach stable state."""
    waiter = ecs_client.get_waiter('services_stable')
    waiter.wait(
        cluster=cluster_name,
        services=[service_name],
        WaiterConfig={'Delay': 15, 'MaxAttempts': 40}
    )


def send_notification(config, cluster_name, service_name, result):
    """Send email notification about recycling completion."""
    content = f"""
    <html>
    <body>
        <h2>ECS Task Recycle Completed</h2>
        <p><strong>Cluster:</strong> {cluster_name}</p>
        <p><strong>Service:</strong> {service_name}</p>
        <p><strong>Tasks Recycled:</strong> {result['tasks_recycled']}</p>
        <p><strong>Timestamp:</strong> {result['timestamp']}</p>
    </body>
    </html>
    """
    
    try:
        send_email(config['smtpCredentials'], config['emailNotification'], content)
        logger.info("Notification sent successfully")
    except Exception as e:
        logger.warning(f"Failed to send notification: {str(e)}")
