"""EC2 event handlers for detecting public resource exposure."""

import boto3
from typing import Dict, Any, List
from core.event_types import EventDetail
from core.constants import INGRESS_WHITELIST_PORTS, EGRESS_WHITELIST_PORTS
from utils.aws_helpers import is_subnet_public, check_security_group_public_access
from utils.logger import setup_logger

logger = setup_logger(__name__)


def handle_ec2_public_instance(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Detect EC2 instances launched in public subnets."""
    logger.info("Checking for public EC2 instances")

    items = (event['detail']
             .get("responseElements", {})
             .get("instancesSet", {})
             .get("items", []))
    if not items:
        return []

    region = event['detail']["awsRegion"]
    ec2_client = boto3.client('ec2', region_name=region)
    violations = []

    for item in items:
        instance_id = item.get("instanceId")
        subnet_id = item.get("subnetId")
        if not instance_id or not subnet_id:
            continue
        if is_subnet_public(ec2_client, subnet_id):
            violations.append(EventDetail(
                title=f"EC2 instance {instance_id} launched in public subnet {subnet_id}",
                source_ip_address=event['detail']["sourceIPAddress"],
                event_source=event['detail']['eventSource'],
                event_name=event['detail']['eventName'],
                resource_name=instance_id,
                resource_value=subnet_id
            ))

    logger.info(f"Found {len(violations)} public EC2 instances")
    return violations


def handle_ec2_public_snapshot(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Detect snapshots being shared publicly or with other accounts."""
    logger.info("Checking for public EC2 snapshots")

    request_params = event['detail'].get("requestParameters", {})
    add_items = (request_params
                 .get("createVolumePermission", {})
                 .get("add", {})
                 .get("items", []))

    snapshot_id = request_params.get('snapshotId', '')
    ip = event['detail'].get("sourceIPAddress", "")
    violations = []

    for item in add_items:
        if item.get("group") == "all" or "userId" in item:
            target = item.get("group", item.get("userId", ""))
            violations.append(EventDetail(
                title=f"EC2 snapshot {snapshot_id} shared with {target}",
                source_ip_address=ip,
                event_source=event['detail']['eventSource'],
                event_name=event['detail']['eventName'],
                resource_name=snapshot_id,
                resource_value=target
            ))

    logger.info(f"Found {len(violations)} public snapshots")
    return violations


def handle_ec2_public_ami(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Detect AMIs being shared with other accounts."""
    logger.info("Checking for public EC2 AMIs")

    request_params = event['detail'].get("requestParameters", {})
    add_items = (request_params
                 .get("launchPermission", {})
                 .get("add", {})
                 .get("items", []))

    image_id = request_params.get('imageId', '')
    ip = event['detail'].get("sourceIPAddress", "")
    violations = []

    for item in add_items:
        if "userId" in item:
            violations.append(EventDetail(
                title=f"EC2 AMI {image_id} shared with account {item['userId']}",
                source_ip_address=ip,
                event_source=event['detail']['eventSource'],
                event_name=event['detail']['eventName'],
                resource_name=image_id,
                resource_value=item["userId"]
            ))

    logger.info(f"Found {len(violations)} public AMIs")
    return violations


def handle_ec2_public_security_group(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Detect newly created security groups with public access rules."""
    logger.info("Checking for public security groups")

    sg_id = event['detail'].get("responseElements", {}).get("groupId")
    if not sg_id:
        return []

    region = event['detail']["awsRegion"]
    ec2_client = boto3.client('ec2', region_name=region)

    has_public, rule_types = check_security_group_public_access(
        ec2_client, sg_id, INGRESS_WHITELIST_PORTS, EGRESS_WHITELIST_PORTS
    )

    if has_public:
        desc = f"Internet allowed in {' and '.join(rule_types)}"
        return [EventDetail(
            title=f"Public security group {sg_id} created: {desc}",
            source_ip_address=event['detail']["sourceIPAddress"],
            event_source=event['detail']['eventSource'],
            event_name=event['detail']['eventName'],
            resource_name=sg_id,
            resource_value=desc
        )]

    return []
