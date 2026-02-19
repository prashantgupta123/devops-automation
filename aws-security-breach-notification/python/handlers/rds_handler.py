"""RDS event handlers for detecting public database exposure."""

import boto3
from typing import Dict, Any, List
from core.event_types import EventDetail
from utils.aws_helpers import is_subnet_public
from utils.logger import setup_logger

logger = setup_logger(__name__)


def handle_rds_public_instance(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Detect RDS instances created in public subnets."""
    logger.info("Checking for public RDS instances")

    response_elements = event['detail'].get("responseElements", {})
    db_subnet_group = response_elements.get("dBSubnetGroup", {})
    subnets = db_subnet_group.get("subnets", [])
    if not subnets:
        return []

    region = event['detail']["awsRegion"]
    ec2_client = boto3.client('ec2', region_name=region)
    db_id = response_elements.get("dBInstanceIdentifier", "")
    subnet_group_name = db_subnet_group.get("dBSubnetGroupName", "")

    for subnet in subnets:
        subnet_id = subnet.get("subnetIdentifier")
        if subnet_id and is_subnet_public(ec2_client, subnet_id):
            return [EventDetail(
                title=f"RDS instance {db_id} created in public subnet group {subnet_group_name}",
                source_ip_address=event['detail']["sourceIPAddress"],
                event_source=event['detail']['eventSource'],
                event_name=event['detail']['eventName'],
                resource_name=db_id,
                resource_value=subnet_group_name
            )]

    return []


def handle_rds_public_snapshot(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """
    Detect RDS snapshots being shared publicly.
    Covers: ModifyDBClusterSnapshotAttribute, ModifyDBSnapshotAttribute
    """
    logger.info("Checking for public RDS snapshots")

    detail = event['detail']
    request_params = detail.get("requestParameters", {})
    event_name = detail['eventName']

    if event_name == "ModifyDBClusterSnapshotAttribute":
        resource_name = request_params.get('dBClusterSnapshotIdentifier', '')
    else:
        resource_name = request_params.get('dBSnapshotIdentifier', '')

    if request_params.get("attributeName") != "restore":
        return []

    values_to_add = request_params.get("valuesToAdd", [])
    if not values_to_add:
        return []

    targets = ', '.join(values_to_add)
    return [EventDetail(
        title=f"RDS snapshot {resource_name} shared with {targets}",
        source_ip_address=detail["sourceIPAddress"],
        event_source=detail['eventSource'],
        event_name=detail['eventName'],
        resource_name=resource_name,
        resource_value=targets
    )]
