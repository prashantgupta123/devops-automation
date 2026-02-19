"""Secrets Manager event handlers for secret deletion."""

from typing import Dict, Any, List
from core.event_types import EventDetail
from utils.logger import setup_logger

logger = setup_logger(__name__)


def handle_secret_deletion(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when a secret is deleted from Secrets Manager."""
    logger.info("Processing secret deletion")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    secret_name = request_params.get('name', '') or request_params.get('secretId', '')
    
    return [EventDetail(
        title=f"Secret {secret_name} deleted",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail.get('eventSource', ''),
        event_name=detail['eventName'],
        resource_name=secret_name
    )]
