"""AWS Config event handlers for detecting compliance monitoring tampering."""

from typing import Dict, Any, List
from core.event_types import EventDetail
from utils.logger import setup_logger

logger = setup_logger(__name__)


def handle_delete_configuration_recorder(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when AWS Config configuration recorder is deleted."""
    logger.info("Processing Config recorder deletion")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    recorder_name = request_params.get('configurationRecorderName', 'Unknown')
    
    return [EventDetail(
        title=f"AWS Config recorder '{recorder_name}' deleted - compliance monitoring disabled",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail['eventSource'],
        event_name=detail['eventName'],
        resource_name=recorder_name,
        resource_value="Recorder deleted"
    )]


def handle_stop_configuration_recorder(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when AWS Config configuration recorder is stopped."""
    logger.info("Processing Config recorder stop")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    recorder_name = request_params.get('configurationRecorderName', 'Unknown')
    
    return [EventDetail(
        title=f"AWS Config recorder '{recorder_name}' stopped - compliance monitoring paused",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail['eventSource'],
        event_name=detail['eventName'],
        resource_name=recorder_name,
        resource_value="Recorder stopped"
    )]


def handle_delete_delivery_channel(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when AWS Config delivery channel is deleted."""
    logger.info("Processing Config delivery channel deletion")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    channel_name = request_params.get('deliveryChannelName', 'Unknown')
    
    return [EventDetail(
        title=f"AWS Config delivery channel '{channel_name}' deleted - config data delivery stopped",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail['eventSource'],
        event_name=detail['eventName'],
        resource_name=channel_name,
        resource_value="Delivery channel deleted"
    )]


def handle_delete_config_rule(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when an AWS Config rule is deleted."""
    logger.info("Processing Config rule deletion")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    rule_name = request_params.get('configRuleName', 'Unknown')
    
    return [EventDetail(
        title=f"AWS Config rule '{rule_name}' deleted - compliance check removed",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail['eventSource'],
        event_name=detail['eventName'],
        resource_name=rule_name,
        resource_value="Config rule deleted"
    )]


def handle_delete_aggregation_authorization(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when Config aggregation authorization is deleted."""
    logger.info("Processing Config aggregation authorization deletion")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    authorized_account = request_params.get('authorizedAccountId', 'Unknown')
    authorized_region = request_params.get('authorizedAwsRegion', 'Unknown')
    
    return [EventDetail(
        title=f"AWS Config aggregation authorization deleted for account {authorized_account} in {authorized_region}",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail['eventSource'],
        event_name=detail['eventName'],
        resource_name=authorized_account,
        resource_value=f"Region: {authorized_region}"
    )]


def handle_delete_configuration_aggregator(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when Config aggregator is deleted."""
    logger.info("Processing Config aggregator deletion")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    aggregator_name = request_params.get('configurationAggregatorName', 'Unknown')
    
    return [EventDetail(
        title=f"AWS Config aggregator '{aggregator_name}' deleted - multi-account/region monitoring disabled",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail['eventSource'],
        event_name=detail['eventName'],
        resource_name=aggregator_name,
        resource_value="Aggregator deleted"
    )]


def handle_delete_remediation_configuration(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when Config remediation configuration is deleted."""
    logger.info("Processing Config remediation deletion")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    rule_name = request_params.get('configRuleName', 'Unknown')
    
    return [EventDetail(
        title=f"AWS Config remediation configuration deleted for rule '{rule_name}'",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail['eventSource'],
        event_name=detail['eventName'],
        resource_name=rule_name,
        resource_value="Auto-remediation disabled"
    )]


def handle_put_config_rule(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Info: Track when Config rules are created or modified."""
    logger.info("Processing Config rule creation/modification")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    config_rule = request_params.get('configRule', {})
    rule_name = config_rule.get('configRuleName', 'Unknown')
    rule_state = config_rule.get('configRuleState', 'ACTIVE')
    
    # Only alert if rule is being disabled
    if rule_state != 'ACTIVE':
        return [EventDetail(
            title=f"AWS Config rule '{rule_name}' set to state: {rule_state}",
            source_ip_address=detail.get("sourceIPAddress", ""),
            event_source=detail['eventSource'],
            event_name=detail['eventName'],
            resource_name=rule_name,
            resource_value=f"State: {rule_state}"
        )]
    
    return []
