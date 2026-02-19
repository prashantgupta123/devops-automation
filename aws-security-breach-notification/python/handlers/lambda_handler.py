"""Lambda event handlers for tracking function changes."""

from typing import Dict, Any, List
from core.event_types import EventDetail
from utils.logger import setup_logger

logger = setup_logger(__name__)

_TITLES = {
    "CreateFunction20150331": "New Lambda function created",
    "UpdateFunctionCode20150331v2": "Lambda function code updated",
    "UpdateFunctionConfiguration20150331v2": "Lambda function configuration updated",
}


def handle_lambda_function_event(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """
    Track Lambda function create/update events.
    Skips events for the monitoring function itself to prevent recursion.
    """
    logger.info("Processing Lambda function event")

    detail = event['detail']
    request_params = detail.get('requestParameters', {})

    # Avoid recursion: skip if this event is about our own function
    if isinstance(request_params, dict):
        function_name = request_params.get('functionName', '')
        if function_name == context.invoked_function_arn:
            logger.info("Skipping self-referencing event")
            return []

    event_name = detail['eventName']
    title = _TITLES.get(event_name, f"Lambda event: {event_name}")

    return [EventDetail(title=title)]
