"""AWS helper utilities for security monitoring."""

import boto3
from typing import List, Dict, Any, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)


def is_subnet_public(ec2_client: Any, subnet_id: str) -> bool:
    """
    Check if a subnet is public by analyzing its route table.
    A subnet is public if it has a route to an Internet Gateway (0.0.0.0/0 -> igw-*).
    
    Args:
        ec2_client: Boto3 EC2 client
        subnet_id: Subnet ID to check
    
    Returns:
        True if subnet is public, False otherwise
    """
    try:
        response = ec2_client.describe_route_tables(
            Filters=[{"Name": "association.subnet-id", "Values": [subnet_id]}]
        )
        
        for route_table in response.get("RouteTables", []):
            for route in route_table.get("Routes", []):
                dest_cidr = route.get("DestinationCidrBlock", "")
                gateway_id = route.get("GatewayId", "")
                
                if dest_cidr == "0.0.0.0/0" and gateway_id.startswith("igw-"):
                    return True
        
        return False
    except Exception as e:
        logger.error(f"Error checking subnet {subnet_id} public status: {e}")
        return False


def check_security_group_public_access(
    ec2_client: Any,
    security_group_id: str,
    ingress_whitelist: List[int],
    egress_whitelist: List[int]
) -> tuple[bool, set[str]]:
    """
    Check if security group has public access rules.
    
    Args:
        ec2_client: Boto3 EC2 client
        security_group_id: Security group ID
        ingress_whitelist: Ports to ignore for ingress
        egress_whitelist: Ports to ignore for egress
    
    Returns:
        Tuple of (has_public_access, set of rule types with public access)
    """
    try:
        response = ec2_client.describe_security_groups(GroupIds=[security_group_id])
        security_groups = response.get('SecurityGroups', [])
        
        if not security_groups:
            return False, set()
        
        sg = security_groups[0]
        public_access = False
        rule_types = set()
        
        # Check ingress rules
        for rule in sg.get('IpPermissions', []):
            if _is_rule_public(rule, ingress_whitelist):
                public_access = True
                rule_types.add("Ingress")
        
        # Check egress rules
        for rule in sg.get('IpPermissionsEgress', []):
            if _is_rule_public(rule, egress_whitelist):
                public_access = True
                rule_types.add("Egress")
        
        return public_access, rule_types
    except Exception as e:
        logger.error(f"Error checking security group {security_group_id}: {e}")
        return False, set()


def _is_rule_public(rule: Dict[str, Any], whitelist: List[int]) -> bool:
    """Check if a security group rule allows public access."""
    # Check if rule allows all protocols or non-whitelisted ports
    if rule.get('IpProtocol') == '-1':
        is_public_port = True
    else:
        from_port = rule.get('FromPort', 0)
        is_public_port = from_port not in whitelist
    
    if not is_public_port:
        return False
    
    # Check for public CIDR blocks
    for ip_range in rule.get('IpRanges', []):
        if ip_range.get('CidrIp') == '0.0.0.0/0':
            return True
    
    for ipv6_range in rule.get('Ipv6Ranges', []):
        if ipv6_range.get('CidrIpv6') == '::/0':
            return True
    
    return False


def extract_user_from_event(event: Dict[str, Any]) -> str:
    """
    Extract username from CloudTrail event.
    
    Args:
        event: CloudTrail event
    
    Returns:
        Username or user type
    """
    user_identity = event.get('detail', {}).get('userIdentity', {})
    user_type = user_identity.get('type', 'Unknown')
    
    if user_type == "Root":
        return "Root"
    
    arn = user_identity.get('arn', '')
    if arn:
        return arn.split('/')[-1]
    
    return user_type
