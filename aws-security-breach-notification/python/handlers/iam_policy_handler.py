"""IAM policy event handlers for detecting privilege escalation and overly permissive policies."""

from typing import Dict, Any, List
import json
from core.event_types import EventDetail
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Dangerous managed policies
DANGEROUS_POLICIES = [
    'AdministratorAccess',
    'PowerUserAccess',
    'IAMFullAccess',
    'SecurityAudit'
]

# Dangerous actions that could lead to privilege escalation
DANGEROUS_ACTIONS = [
    'iam:*',
    'iam:CreateAccessKey',
    'iam:CreateLoginProfile',
    'iam:UpdateAssumeRolePolicy',
    'iam:AttachUserPolicy',
    'iam:AttachRolePolicy',
    'iam:PutUserPolicy',
    'iam:PutRolePolicy',
    'sts:AssumeRole',
    'lambda:CreateFunction',
    'lambda:UpdateFunctionCode',
    'ec2:RunInstances'
]


def handle_put_user_policy(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Detect inline policies attached to users with dangerous permissions."""
    logger.info("Processing inline user policy creation")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    user_name = request_params.get('userName', 'Unknown')
    policy_name = request_params.get('policyName', 'Unknown')
    policy_document = request_params.get('policyDocument', '')
    
    violations = []
    
    # Check for wildcard permissions
    if '"*"' in policy_document or '"Action": "*"' in policy_document:
        violations.append(EventDetail(
            title=f"Inline policy '{policy_name}' with wildcard permissions attached to user {user_name}",
            source_ip_address=detail.get("sourceIPAddress", ""),
            event_source=detail['eventSource'],
            event_name=detail['eventName'],
            resource_name=user_name,
            resource_value=f"Policy: {policy_name}"
        ))
    
    # Check for dangerous actions
    for action in DANGEROUS_ACTIONS:
        if action in policy_document:
            violations.append(EventDetail(
                title=f"Inline policy '{policy_name}' with dangerous action '{action}' attached to user {user_name}",
                source_ip_address=detail.get("sourceIPAddress", ""),
                event_source=detail['eventSource'],
                event_name=detail['eventName'],
                resource_name=user_name,
                resource_value=f"Policy: {policy_name}, Action: {action}"
            ))
            break  # Only report once per policy
    
    logger.info(f"Found {len(violations)} inline user policy violations")
    return violations


def handle_put_role_policy(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Detect inline policies attached to roles with dangerous permissions."""
    logger.info("Processing inline role policy creation")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    role_name = request_params.get('roleName', 'Unknown')
    policy_name = request_params.get('policyName', 'Unknown')
    policy_document = request_params.get('policyDocument', '')
    
    violations = []
    
    # Check for wildcard permissions
    if '"*"' in policy_document or '"Action": "*"' in policy_document:
        violations.append(EventDetail(
            title=f"Inline policy '{policy_name}' with wildcard permissions attached to role {role_name}",
            source_ip_address=detail.get("sourceIPAddress", ""),
            event_source=detail['eventSource'],
            event_name=detail['eventName'],
            resource_name=role_name,
            resource_value=f"Policy: {policy_name}"
        ))
    
    # Check for dangerous actions
    for action in DANGEROUS_ACTIONS:
        if action in policy_document:
            violations.append(EventDetail(
                title=f"Inline policy '{policy_name}' with dangerous action '{action}' attached to role {role_name}",
                source_ip_address=detail.get("sourceIPAddress", ""),
                event_source=detail['eventSource'],
                event_name=detail['eventName'],
                resource_name=role_name,
                resource_value=f"Policy: {policy_name}, Action: {action}"
            ))
            break
    
    logger.info(f"Found {len(violations)} inline role policy violations")
    return violations


def handle_attach_user_policy(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Detect dangerous managed policies attached to users."""
    logger.info("Processing managed policy attachment to user")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    user_name = request_params.get('userName', 'Unknown')
    policy_arn = request_params.get('policyArn', '')
    
    violations = []
    
    # Check if it's a dangerous managed policy
    for dangerous_policy in DANGEROUS_POLICIES:
        if dangerous_policy in policy_arn:
            violations.append(EventDetail(
                title=f"Dangerous managed policy '{dangerous_policy}' attached to user {user_name}",
                source_ip_address=detail.get("sourceIPAddress", ""),
                event_source=detail['eventSource'],
                event_name=detail['eventName'],
                resource_name=user_name,
                resource_value=policy_arn
            ))
            break
    
    logger.info(f"Found {len(violations)} user policy attachment violations")
    return violations


def handle_attach_role_policy(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Detect dangerous managed policies attached to roles."""
    logger.info("Processing managed policy attachment to role")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    role_name = request_params.get('roleName', 'Unknown')
    policy_arn = request_params.get('policyArn', '')
    
    violations = []
    
    # Check if it's a dangerous managed policy
    for dangerous_policy in DANGEROUS_POLICIES:
        if dangerous_policy in policy_arn:
            violations.append(EventDetail(
                title=f"Dangerous managed policy '{dangerous_policy}' attached to role {role_name}",
                source_ip_address=detail.get("sourceIPAddress", ""),
                event_source=detail['eventSource'],
                event_name=detail['eventName'],
                resource_name=role_name,
                resource_value=policy_arn
            ))
            break
    
    logger.info(f"Found {len(violations)} role policy attachment violations")
    return violations


def handle_create_policy(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Detect creation of overly permissive custom policies."""
    logger.info("Processing custom policy creation")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    policy_name = request_params.get('policyName', 'Unknown')
    policy_document = request_params.get('policyDocument', '')
    
    violations = []
    
    # Check for wildcard permissions
    if '"*"' in policy_document or '"Action": "*"' in policy_document:
        violations.append(EventDetail(
            title=f"Custom policy '{policy_name}' created with wildcard permissions",
            source_ip_address=detail.get("sourceIPAddress", ""),
            event_source=detail['eventSource'],
            event_name=detail['eventName'],
            resource_name=policy_name,
            resource_value="Wildcard permissions"
        ))
    
    # Check for dangerous actions
    for action in DANGEROUS_ACTIONS:
        if action in policy_document:
            violations.append(EventDetail(
                title=f"Custom policy '{policy_name}' created with dangerous action '{action}'",
                source_ip_address=detail.get("sourceIPAddress", ""),
                event_source=detail['eventSource'],
                event_name=detail['eventName'],
                resource_name=policy_name,
                resource_value=f"Action: {action}"
            ))
            break
    
    logger.info(f"Found {len(violations)} custom policy violations")
    return violations


def handle_update_assume_role_policy(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Detect changes to role trust policies (assume role policies)."""
    logger.info("Processing assume role policy update")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    role_name = request_params.get('roleName', 'Unknown')
    policy_document = request_params.get('policyDocument', '')
    
    violations = []
    
    # Check for wildcard principal
    if '"Principal": "*"' in policy_document or '"AWS": "*"' in policy_document:
        violations.append(EventDetail(
            title=f"Role {role_name} trust policy updated with wildcard principal (public access)",
            source_ip_address=detail.get("sourceIPAddress", ""),
            event_source=detail['eventSource'],
            event_name=detail['eventName'],
            resource_name=role_name,
            resource_value="Wildcard principal"
        ))
    
    # Check for cross-account access
    try:
        policy_obj = json.loads(policy_document) if isinstance(policy_document, str) else policy_document
        for statement in policy_obj.get('Statement', []):
            principal = statement.get('Principal', {})
            if isinstance(principal, dict):
                aws_principals = principal.get('AWS', [])
                if isinstance(aws_principals, str):
                    aws_principals = [aws_principals]
                
                for principal_arn in aws_principals:
                    if 'arn:aws:iam::' in principal_arn and '::root' in principal_arn:
                        violations.append(EventDetail(
                            title=f"Role {role_name} trust policy updated with cross-account access",
                            source_ip_address=detail.get("sourceIPAddress", ""),
                            event_source=detail['eventSource'],
                            event_name=detail['eventName'],
                            resource_name=role_name,
                            resource_value=f"Cross-account: {principal_arn}"
                        ))
                        break
    except (json.JSONDecodeError, AttributeError, KeyError) as e:
        logger.warning(f"Failed to parse assume role policy: {e}")
    
    logger.info(f"Found {len(violations)} assume role policy violations")
    return violations
