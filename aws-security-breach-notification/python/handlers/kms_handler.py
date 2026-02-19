"""KMS event handlers for detecting encryption key security issues."""

from typing import Dict, Any, List
from core.event_types import EventDetail
from utils.logger import setup_logger

logger = setup_logger(__name__)


def handle_schedule_key_deletion(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when a KMS key is scheduled for deletion."""
    logger.info("Processing KMS key deletion schedule")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    key_id = request_params.get('keyId', 'Unknown')
    pending_days = request_params.get('pendingWindowInDays', 'Unknown')
    
    return [EventDetail(
        title=f"KMS key {key_id} scheduled for deletion in {pending_days} days",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail['eventSource'],
        event_name=detail['eventName'],
        resource_name=key_id,
        resource_value=f"Pending deletion: {pending_days} days"
    )]


def handle_disable_key(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when a KMS key is disabled."""
    logger.info("Processing KMS key disable")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    key_id = request_params.get('keyId', 'Unknown')
    
    return [EventDetail(
        title=f"KMS key {key_id} disabled",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail['eventSource'],
        event_name=detail['eventName'],
        resource_name=key_id,
        resource_value="Key disabled"
    )]


def handle_put_key_policy(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when KMS key policy is modified (potential external sharing)."""
    logger.info("Processing KMS key policy change")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    key_id = request_params.get('keyId', 'Unknown')
    policy = request_params.get('policy', '')
    
    violations = []
    
    # Check for external account access
    if '"AWS": "arn:aws:iam::' in policy and '*' not in policy:
        # Extract account IDs from policy (simplified check)
        if 'Principal' in policy:
            violations.append(EventDetail(
                title=f"KMS key {key_id} policy modified - potential external sharing",
                source_ip_address=detail.get("sourceIPAddress", ""),
                event_source=detail['eventSource'],
                event_name=detail['eventName'],
                resource_name=key_id,
                resource_value="Policy modified"
            ))
    
    # Check for overly permissive policies
    if '"*"' in policy or '"kms:*"' in policy:
        violations.append(EventDetail(
            title=f"KMS key {key_id} policy set to overly permissive (wildcard permissions)",
            source_ip_address=detail.get("sourceIPAddress", ""),
            event_source=detail['eventSource'],
            event_name=detail['eventName'],
            resource_name=key_id,
            resource_value="Wildcard permissions detected"
        ))
    
    logger.info(f"Found {len(violations)} KMS policy violations")
    return violations


def handle_delete_alias(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when a KMS key alias is deleted."""
    logger.info("Processing KMS alias deletion")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    alias_name = request_params.get('aliasName', 'Unknown')
    
    return [EventDetail(
        title=f"KMS alias {alias_name} deleted",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail['eventSource'],
        event_name=detail['eventName'],
        resource_name=alias_name,
        resource_value="Alias deleted"
    )]


def handle_cancel_key_deletion(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Info: KMS key deletion cancelled (positive event)."""
    logger.info("Processing KMS key deletion cancellation")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    key_id = request_params.get('keyId', 'Unknown')
    
    return [EventDetail(
        title=f"KMS key {key_id} deletion cancelled (restored)",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail['eventSource'],
        event_name=detail['eventName'],
        resource_name=key_id,
        resource_value="Deletion cancelled"
    )]
