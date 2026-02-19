"""CloudWatch event handlers for detecting log tampering and monitoring changes."""

from typing import Dict, Any, List
from core.event_types import EventDetail
from utils.logger import setup_logger

logger = setup_logger(__name__)


def handle_delete_log_group(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when a CloudWatch log group is deleted."""
    logger.info("Processing CloudWatch log group deletion")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    log_group_name = request_params.get('logGroupName', 'Unknown')
    
    return [EventDetail(
        title=f"CloudWatch log group '{log_group_name}' deleted - logs lost",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail['eventSource'],
        event_name=detail['eventName'],
        resource_name=log_group_name,
        resource_value="Log group deleted"
    )]


def handle_delete_log_stream(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when a CloudWatch log stream is deleted."""
    logger.info("Processing CloudWatch log stream deletion")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    log_group_name = request_params.get('logGroupName', 'Unknown')
    log_stream_name = request_params.get('logStreamName', 'Unknown')
    
    return [EventDetail(
        title=f"CloudWatch log stream '{log_stream_name}' deleted from group '{log_group_name}'",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail['eventSource'],
        event_name=detail['eventName'],
        resource_name=log_stream_name,
        resource_value=f"Log group: {log_group_name}"
    )]



def handle_delete_metric_alarm(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when a CloudWatch metric alarm is deleted."""
    logger.info("Processing CloudWatch alarm deletion")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    alarm_names = request_params.get('alarmNames', [])
    
    violations = []
    for alarm_name in alarm_names:
        violations.append(EventDetail(
            title=f"CloudWatch alarm '{alarm_name}' deleted - monitoring disabled",
            source_ip_address=detail.get("sourceIPAddress", ""),
            event_source=detail['eventSource'],
            event_name=detail['eventName'],
            resource_name=alarm_name,
            resource_value="Alarm deleted"
        ))
    
    logger.info(f"Found {len(violations)} alarm deletions")
    return violations


def handle_disable_alarm_actions(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when CloudWatch alarm actions are disabled."""
    logger.info("Processing CloudWatch alarm action disable")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    alarm_names = request_params.get('alarmNames', [])
    
    violations = []
    for alarm_name in alarm_names:
        violations.append(EventDetail(
            title=f"CloudWatch alarm actions disabled for '{alarm_name}' - alerts stopped",
            source_ip_address=detail.get("sourceIPAddress", ""),
            event_source=detail['eventSource'],
            event_name=detail['eventName'],
            resource_name=alarm_name,
            resource_value="Actions disabled"
        ))
    
    logger.info(f"Found {len(violations)} alarm action disables")
    return violations


def handle_delete_metric_filter(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when a CloudWatch metric filter is deleted."""
    logger.info("Processing CloudWatch metric filter deletion")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    filter_name = request_params.get('filterName', 'Unknown')
    log_group_name = request_params.get('logGroupName', 'Unknown')
    
    return [EventDetail(
        title=f"CloudWatch metric filter '{filter_name}' deleted from log group '{log_group_name}'",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail['eventSource'],
        event_name=detail['eventName'],
        resource_name=filter_name,
        resource_value=f"Log group: {log_group_name}"
    )]


def handle_delete_subscription_filter(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when a CloudWatch subscription filter is deleted."""
    logger.info("Processing CloudWatch subscription filter deletion")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    filter_name = request_params.get('filterName', 'Unknown')
    log_group_name = request_params.get('logGroupName', 'Unknown')
    
    return [EventDetail(
        title=f"CloudWatch subscription filter '{filter_name}' deleted from log group '{log_group_name}'",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail['eventSource'],
        event_name=detail['eventName'],
        resource_name=filter_name,
        resource_value=f"Log group: {log_group_name}"
    )]


def handle_put_retention_policy(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when CloudWatch log retention is reduced."""
    logger.info("Processing CloudWatch log retention change")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    log_group_name = request_params.get('logGroupName', 'Unknown')
    retention_days = request_params.get('retentionInDays', 'Unknown')
    
    # Alert if retention is set to less than 30 days
    if isinstance(retention_days, int) and retention_days < 30:
        return [EventDetail(
            title=f"CloudWatch log retention reduced to {retention_days} days for '{log_group_name}'",
            source_ip_address=detail.get("sourceIPAddress", ""),
            event_source=detail['eventSource'],
            event_name=detail['eventName'],
            resource_name=log_group_name,
            resource_value=f"Retention: {retention_days} days"
        )]
    
    return []
