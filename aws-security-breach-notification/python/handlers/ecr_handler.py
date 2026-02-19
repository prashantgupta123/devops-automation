"""ECR (Elastic Container Registry) event handlers."""

from typing import Dict, Any, List
from core.event_types import EventDetail
from utils.logger import setup_logger

logger = setup_logger(__name__)


def handle_repository_creation(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when a public ECR repository is created."""
    logger.info("Processing ECR repository creation")
    
    detail = event['detail']
    response_elements = detail.get('responseElements', {})
    repository = response_elements.get('repository', {})
    repo_name = repository.get('repositoryName', '')
    
    return [EventDetail(
        title=f"Public ECR repository {repo_name} created",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail.get('eventSource', ''),
        event_name=detail['eventName'],
        repository_name=repo_name
    )]
