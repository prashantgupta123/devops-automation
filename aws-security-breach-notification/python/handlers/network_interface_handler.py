"""Network Interface event handlers for detecting public IP assignments."""

import boto3
from typing import Dict, Any, List
from core.event_types import EventDetail
from utils.logger import setup_logger
from utils.aws_helpers import is_subnet_public

logger = setup_logger(__name__)


def handle_create_network_interface(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """
    Detect network interfaces created in public subnets.
    Excludes interfaces created for load balancers.
    """
    logger.info("Checking for network interface in public subnet")
    
    detail = event['detail']
    response_elements = detail.get('responseElements', {})
    network_interface = response_elements.get('networkInterface', {})
    
    if not network_interface:
        logger.warning("No network interface found in response")
        return []
    
    network_interface_id = network_interface.get('networkInterfaceId', 'Unknown')
    requester_id = network_interface.get('requesterId', '')
    description = network_interface.get('description', '')
    interface_type = network_interface.get('interfaceType', '')
    subnet_id = network_interface.get('subnetId', 'Unknown')
    
    # Get invokedBy from event detail for service identification
    invoked_by = detail.get('userIdentity', {}).get('invokedBy', '')
    
    # Check if this is for a load balancer
    # Load balancers have specific patterns in requesterId, description, and invokedBy
    load_balancer_indicators = [
        'amazon-elb',
        'ELB',
        'elasticloadbalancing',
        'awselb',
        'load-balancer'
    ]
    
    # Check for load balancer
    is_load_balancer = any(
        indicator.lower() in str(requester_id).lower() or 
        indicator.lower() in str(description).lower() or
        indicator.lower() in str(invoked_by).lower()
        for indicator in load_balancer_indicators
    )
    
    # Also check interface type
    if interface_type in ['network_load_balancer', 'gateway_load_balancer', 'load_balancer']:
        is_load_balancer = True
    
    # Skip only if it's a load balancer
    if is_load_balancer:
        logger.info(f"Network interface {network_interface_id} is for load balancer, skipping")
        return []
    
    # Check if the subnet is public using the helper function
    region = detail.get('awsRegion', 'us-east-1')
    ec2_client = boto3.client('ec2', region_name=region)
    
    if not is_subnet_public(ec2_client, subnet_id):
        logger.info(f"Network interface {network_interface_id} is in private subnet {subnet_id}")
        return []
    
    # Get additional context
    vpc_id = network_interface.get('vpcId', 'Unknown')
    availability_zone = network_interface.get('availabilityZone', 'Unknown')
    attachment = network_interface.get('attachment', {})
    instance_id = attachment.get('instanceId', 'Not attached')
    private_ip = network_interface.get('privateIpAddress', 'Unknown')
    
    # Build violation message
    violation_title = (
        f"Network interface {network_interface_id} created in public subnet {subnet_id}"
    )
    
    if instance_id != 'Not attached':
        violation_title += f" (attached to instance {instance_id})"
    
    # Add service context if available
    if 'ecs.amazonaws.com' in str(invoked_by):
        violation_title += " [ECS Service]"
    elif 'lambda.amazonaws.com' in str(invoked_by):
        violation_title += " [Lambda Function]"
    
    return [EventDetail(
        title=violation_title,
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail['eventSource'],
        event_name=detail['eventName'],
        resource_name=network_interface_id,
        resource_value=f"Private IP: {private_ip}, Subnet: {subnet_id}, VPC: {vpc_id}, AZ: {availability_zone}"
    )]


def handle_associate_address(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """
    Detect when an Elastic IP is associated with a network interface.
    Excludes associations with load balancers.
    """
    logger.info("Checking for Elastic IP association with network interface")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    response_elements = detail.get('responseElements', {})
    
    network_interface_id = request_params.get('networkInterfaceId')
    allocation_id = request_params.get('allocationId', 'Unknown')
    public_ip = request_params.get('publicIp', 'Unknown')
    association_id = response_elements.get('associationId', 'Unknown')
    
    if not network_interface_id:
        # Might be associated with instance directly
        instance_id = request_params.get('instanceId')
        if instance_id:
            logger.info(f"Elastic IP associated with instance {instance_id} directly")
            return [EventDetail(
                title=f"Elastic IP {public_ip} associated with instance {instance_id}",
                source_ip_address=detail.get("sourceIPAddress", ""),
                event_source=detail['eventSource'],
                event_name=detail['eventName'],
                resource_name=instance_id,
                resource_value=f"Elastic IP: {public_ip}, Allocation: {allocation_id}"
            )]
        return []
    
    # Check if this network interface belongs to a load balancer
    region = detail.get('awsRegion', 'us-east-1')
    ec2_client = boto3.client('ec2', region_name=region)
    
    try:
        response = ec2_client.describe_network_interfaces(
            NetworkInterfaceIds=[network_interface_id]
        )
        
        if response['NetworkInterfaces']:
            eni = response['NetworkInterfaces'][0]
            requester_id = eni.get('RequesterId', '')
            description = eni.get('Description', '')
            interface_type = eni.get('InterfaceType', '')
            
            # Get invokedBy from event detail
            invoked_by = detail.get('userIdentity', {}).get('invokedBy', '')
            
            # Check for load balancer indicators
            load_balancer_indicators = [
                'amazon-elb',
                'ELB',
                'elasticloadbalancing',
                'awselb',
                'load-balancer'
            ]
            
            # Check for load balancer
            is_load_balancer = any(
                indicator.lower() in str(requester_id).lower() or 
                indicator.lower() in str(description).lower() or
                indicator.lower() in str(invoked_by).lower()
                for indicator in load_balancer_indicators
            )
            
            if interface_type in ['network_load_balancer', 'gateway_load_balancer', 'load_balancer']:
                is_load_balancer = True
            
            if is_load_balancer:
                logger.info(f"Network interface {network_interface_id} is for load balancer, skipping")
                return []
            
            # Get additional context
            subnet_id = eni.get('SubnetId', 'Unknown')
            vpc_id = eni.get('VpcId', 'Unknown')
            attachment = eni.get('Attachment', {})
            instance_id = attachment.get('InstanceId', 'Not attached')
            
            violation_title = (
                f"Elastic IP {public_ip} associated with network interface {network_interface_id}"
            )
            
            if instance_id != 'Not attached':
                violation_title += f" (instance {instance_id})"
            
            return [EventDetail(
                title=violation_title,
                source_ip_address=detail.get("sourceIPAddress", ""),
                event_source=detail['eventSource'],
                event_name=detail['eventName'],
                resource_name=network_interface_id,
                resource_value=f"Elastic IP: {public_ip}, Subnet: {subnet_id}, VPC: {vpc_id}"
            )]
    
    except Exception as e:
        logger.error(f"Error describing network interface {network_interface_id}: {e}")
        # Still report the association even if we can't verify it's not a load balancer
        return [EventDetail(
            title=f"Elastic IP {public_ip} associated with network interface {network_interface_id}",
            source_ip_address=detail.get("sourceIPAddress", ""),
            event_source=detail['eventSource'],
            event_name=detail['eventName'],
            resource_name=network_interface_id,
            resource_value=f"Elastic IP: {public_ip}, Allocation: {allocation_id}"
        )]
    
    return []


def handle_modify_network_interface_attribute(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """
    Track when network interface attributes are modified.
    This can include security group changes or source/dest check modifications.
    """
    logger.info("Processing network interface attribute modification")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    network_interface_id = request_params.get('networkInterfaceId', 'Unknown')
    
    # Check what attribute was modified
    violations = []
    
    # Check if source/dest check was disabled (can be used for NAT)
    if 'sourceDestCheck' in request_params:
        source_dest_check = request_params['sourceDestCheck'].get('value', True)
        if not source_dest_check:
            violations.append(EventDetail(
                title=f"Network interface {network_interface_id} source/dest check disabled",
                source_ip_address=detail.get("sourceIPAddress", ""),
                event_source=detail['eventSource'],
                event_name=detail['eventName'],
                resource_name=network_interface_id,
                resource_value="Source/Dest check disabled (NAT/routing enabled)"
            ))
    
    # Check if security groups were modified
    if 'groupSet' in request_params:
        group_set = request_params['groupSet'].get('items', [])
        group_ids = [g.get('groupId', '') for g in group_set if isinstance(g, dict)]
        if group_ids:
            violations.append(EventDetail(
                title=f"Network interface {network_interface_id} security groups modified",
                source_ip_address=detail.get("sourceIPAddress", ""),
                event_source=detail['eventSource'],
                event_name=detail['eventName'],
                resource_name=network_interface_id,
                resource_value=f"Security groups: {', '.join(group_ids)}"
            ))
    
    logger.info(f"Found {len(violations)} network interface attribute violations")
    return violations
