"""EBS volume event handlers for detecting unencrypted storage."""

import boto3
from typing import Dict, Any, List
from core.event_types import EventDetail
from utils.logger import setup_logger

logger = setup_logger(__name__)


def handle_create_volume(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Detect unencrypted EBS volumes being created."""
    logger.info("Checking for unencrypted EBS volume creation")
    
    detail = event['detail']
    response_elements = detail.get('responseElements', {})
    volume_id = response_elements.get('volumeId', 'Unknown')
    encrypted = response_elements.get('encrypted', False)
    size = response_elements.get('size', 'Unknown')
    volume_type = response_elements.get('volumeType', 'Unknown')
    availability_zone = response_elements.get('availabilityZone', 'Unknown')
    
    if not encrypted:
        return [EventDetail(
            title=f"Unencrypted EBS volume {volume_id} created ({size}GB, {volume_type}) in {availability_zone}",
            source_ip_address=detail.get("sourceIPAddress", ""),
            event_source=detail['eventSource'],
            event_name=detail['eventName'],
            resource_name=volume_id,
            resource_value=f"Size: {size}GB, Type: {volume_type}, Encrypted: False"
        )]
    
    return []


def handle_modify_volume_attribute(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when EBS volume attributes are modified."""
    logger.info("Processing EBS volume attribute modification")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    volume_id = request_params.get('volumeId', 'Unknown')
    
    # Track any volume attribute changes
    return [EventDetail(
        title=f"EBS volume {volume_id} attributes modified",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail['eventSource'],
        event_name=detail['eventName'],
        resource_name=volume_id,
        resource_value="Attributes modified"
    )]


def handle_delete_volume(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when an EBS volume is deleted."""
    logger.info("Processing EBS volume deletion")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    volume_id = request_params.get('volumeId', 'Unknown')
    
    return [EventDetail(
        title=f"EBS volume {volume_id} deleted",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail['eventSource'],
        event_name=detail['eventName'],
        resource_name=volume_id,
        resource_value="Volume deleted"
    )]
