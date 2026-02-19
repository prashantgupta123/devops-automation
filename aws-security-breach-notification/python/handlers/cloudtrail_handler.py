"""CloudTrail event handlers for detecting audit trail tampering."""

from typing import Dict, Any, List
from core.event_types import EventDetail
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Map event names to human-readable descriptions
_TITLES = {
    "StopLogging": "CloudTrail logging stopped for {name}",
    "DeleteTrail": "CloudTrail {name} deleted",
}


def handle_cloudtrail_event(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when CloudTrail logging is stopped or a trail is deleted."""
    logger.info("Processing CloudTrail event")

    detail = event['detail']
    trail_name = detail.get('requestParameters', {}).get('name', 'Unknown')
    template = _TITLES.get(detail['eventName'], "CloudTrail event on {name}")

    return [EventDetail(
        title=template.format(name=trail_name),
        source_ip_address=detail.get("sourceIPAddress", ""),
        resource_name=trail_name
    )]
