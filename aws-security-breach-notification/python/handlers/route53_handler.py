"""Route53 event handlers for DNS changes."""

from typing import Dict, Any, List
from core.event_types import EventDetail
from utils.logger import setup_logger

logger = setup_logger(__name__)


def handle_hosted_zone_deletion(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when a Route53 hosted zone is deleted."""
    logger.info("Processing hosted zone deletion")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    zone_id = request_params.get('id', '')
    
    return [EventDetail(
        title=f"Hosted zone {zone_id} deleted",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail.get('eventSource', ''),
        event_name=detail['eventName'],
        hosted_zone_name=zone_id
    )]


def handle_record_set_change(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when DNS records are changed in a hosted zone."""
    logger.info("Processing DNS record change")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    zone_id = request_params.get('hostedZoneId', '')
    
    # Extract record name from change batch
    changes = request_params.get('changeBatch', {}).get('changes', [])
    if not changes:
        return []
    
    record = changes[0].get('resourceRecordSet', {}).get('name', '')
    
    return [EventDetail(
        title=f"DNS record {record} changed in hosted zone {zone_id}",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail.get('eventSource', ''),
        event_name=detail['eventName'],
        hosted_zone_id=zone_id,
        record_name=record
    )]
