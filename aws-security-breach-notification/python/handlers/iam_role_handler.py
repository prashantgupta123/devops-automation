"""IAM role event handlers for detecting role creation and modifications."""

from typing import Dict, Any, List
import json
from core.event_types import EventDetail
from utils.logger import setup_logger

logger = setup_logger(__name__)


def handle_create_role(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when a new IAM role is created, especially with external trust relationships."""
    logger.info("Processing IAM role creation")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    role_name = request_params.get('roleName', 'Unknown')
    assume_role_policy = request_params.get('assumeRolePolicyDocument', '')
    
    violations = []
    
    # Always track role creation
    violations.append(EventDetail(
        title=f"IAM role '{role_name}' created",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail['eventSource'],
        event_name=detail['eventName'],
        resource_name=role_name,
        resource_value="Role created"
    ))
    
    # Check for external trust relationships
    try:
        policy_obj = json.loads(assume_role_policy) if isinstance(assume_role_policy, str) else assume_role_policy
        
        for statement in policy_obj.get('Statement', []):
            principal = statement.get('Principal', {})
            
            # Check for wildcard principal
            if principal == '*' or principal.get('AWS') == '*':
                violations.append(EventDetail(
                    title=f"IAM role '{role_name}' created with wildcard principal (public trust)",
                    source_ip_address=detail.get("sourceIPAddress", ""),
                    event_source=detail['eventSource'],
                    event_name=detail['eventName'],
                    resource_name=role_name,
                    resource_value="Wildcard principal"
                ))
            
            # Check for cross-account trust
            if isinstance(principal, dict):
                aws_principals = principal.get('AWS', [])
                if isinstance(aws_principals, str):
                    aws_principals = [aws_principals]
                
                for principal_arn in aws_principals:
                    if 'arn:aws:iam::' in str(principal_arn) and '::root' in str(principal_arn):
                        violations.append(EventDetail(
                            title=f"IAM role '{role_name}' created with cross-account trust",
                            source_ip_address=detail.get("sourceIPAddress", ""),
                            event_source=detail['eventSource'],
                            event_name=detail['eventName'],
                            resource_name=role_name,
                            resource_value=f"Cross-account: {principal_arn}"
                        ))
            
            # Check for external service trust (e.g., third-party services)
            service = principal.get('Service', '')
            if service and not any(aws_service in str(service) for aws_service in 
                                  ['amazonaws.com', 'aws.amazon.com']):
                violations.append(EventDetail(
                    title=f"IAM role '{role_name}' created with external service trust: {service}",
                    source_ip_address=detail.get("sourceIPAddress", ""),
                    event_source=detail['eventSource'],
                    event_name=detail['eventName'],
                    resource_name=role_name,
                    resource_value=f"Service: {service}"
                ))
    
    except (json.JSONDecodeError, AttributeError, KeyError) as e:
        logger.warning(f"Failed to parse assume role policy for {role_name}: {e}")
    
    logger.info(f"Found {len(violations)} role creation violations")
    return violations


def handle_delete_role(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when an IAM role is deleted."""
    logger.info("Processing IAM role deletion")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    role_name = request_params.get('roleName', 'Unknown')
    
    return [EventDetail(
        title=f"IAM role '{role_name}' deleted",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail['eventSource'],
        event_name=detail['eventName'],
        resource_name=role_name,
        resource_value="Role deleted"
    )]


def handle_detach_role_policy(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when a managed policy is detached from a role."""
    logger.info("Processing role policy detachment")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    role_name = request_params.get('roleName', 'Unknown')
    policy_arn = request_params.get('policyArn', 'Unknown')
    
    return [EventDetail(
        title=f"Policy detached from role '{role_name}': {policy_arn}",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail['eventSource'],
        event_name=detail['eventName'],
        resource_name=role_name,
        resource_value=policy_arn
    )]


def handle_delete_role_policy(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when an inline policy is deleted from a role."""
    logger.info("Processing inline role policy deletion")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    role_name = request_params.get('roleName', 'Unknown')
    policy_name = request_params.get('policyName', 'Unknown')
    
    return [EventDetail(
        title=f"Inline policy '{policy_name}' deleted from role '{role_name}'",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail['eventSource'],
        event_name=detail['eventName'],
        resource_name=role_name,
        resource_value=f"Policy: {policy_name}"
    )]
