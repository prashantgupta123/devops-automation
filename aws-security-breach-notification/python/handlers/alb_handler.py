"""ALB event handlers for detecting internet-facing load balancers."""

import boto3
from typing import Dict, Any, List
from core.event_types import EventDetail
from utils.aws_helpers import is_subnet_public
from utils.logger import setup_logger

logger = setup_logger(__name__)


def handle_alb_public(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Detect load balancers created in public subnets (internet-facing)."""
    logger.info("Checking for public load balancers")

    detail = event['detail']
    request_params = detail.get("requestParameters", {})
    subnet_mappings = request_params.get("subnetMappings", [])
    if not subnet_mappings:
        return []

    region = detail["awsRegion"]
    ec2_client = boto3.client('ec2', region_name=region)
    lb_name = request_params.get('name', '')
    violations = []

    for mapping in subnet_mappings:
        subnet_id = mapping.get('subnetId')
        if subnet_id and is_subnet_public(ec2_client, subnet_id):
            violations.append(EventDetail(
                title=f"Public load balancer {lb_name} created in subnet {subnet_id}",
                source_ip_address=detail["sourceIPAddress"],
                event_source=detail['eventSource'],
                event_name=detail['eventName'],
                resource_name=lb_name,
                resource_value=subnet_id
            ))

    logger.info(f"Found {len(violations)} public load balancers")
    return violations
