"""VPC and network resource event handlers."""

from typing import Dict, Any, List, Optional
from core.event_types import EventDetail
from utils.logger import setup_logger

logger = setup_logger(__name__)


def handle_vpc_creation(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when a VPC is created."""
    logger.info("Processing VPC creation")
    
    detail = event['detail']
    response_elements = detail.get('responseElements', {})
    vpc = response_elements.get('vpc', {})
    vpc_id = vpc.get('vpcId', '')
    
    return [EventDetail(
        title=f"VPC {vpc_id} created",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail.get('eventSource', ''),
        event_name=detail['eventName'],
        resource_name=vpc_id
    )]


def handle_vpc_deletion(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when a VPC is deleted."""
    logger.info("Processing VPC deletion")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    vpc_id = request_params.get('vpcId', '')
    
    return [EventDetail(
        title=f"VPC {vpc_id} deleted",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail.get('eventSource', ''),
        event_name=detail['eventName'],
        resource_name=vpc_id
    )]


def handle_subnet_creation(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when a subnet is created."""
    logger.info("Processing subnet creation")
    
    detail = event['detail']
    response_elements = detail.get('responseElements', {})
    subnet = response_elements.get('subnet', {})
    subnet_id = subnet.get('subnetId', '')
    vpc_id = subnet.get('vpcId', '')
    
    # Extract subnet name from tags
    name = None
    for item in subnet.get('tagSet', {}).get('items', []):
        if item.get('key') == 'Name':
            name = item.get('value')
            break
    
    return [EventDetail(
        title=f"Subnet {name or subnet_id} created",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail.get('eventSource', ''),
        event_name=detail['eventName'],
        vpc_id=vpc_id,
        subnet_name=name
    )]


def handle_subnet_deletion(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when a subnet is deleted."""
    logger.info("Processing subnet deletion")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    subnet_id = request_params.get('subnetId', '')
    
    return [EventDetail(
        title=f"Subnet {subnet_id} deleted",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail.get('eventSource', ''),
        event_name=detail['eventName'],
        subnet_id=subnet_id
    )]


def handle_nat_gateway_creation(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when a NAT Gateway is created."""
    logger.info("Processing NAT Gateway creation")
    
    detail = event['detail']
    response_elements = detail.get('responseElements', {})
    nat_response = response_elements.get('CreateNatGatewayResponse', {})
    nat_gateway = nat_response.get('natGateway', {})
    
    gw_id = nat_gateway.get('natGatewayId', '')
    subnet_id = nat_gateway.get('subnetId', '')
    vpc_id = nat_gateway.get('vpcId', '')
    
    return [EventDetail(
        title=f"NAT Gateway {gw_id} created in subnet {subnet_id}",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail.get('eventSource', ''),
        event_name=detail['eventName'],
        nat_gateway_id=gw_id,
        subnet_id=subnet_id,
        vpc_id=vpc_id
    )]


def handle_nat_gateway_deletion(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when a NAT Gateway is deleted."""
    logger.info("Processing NAT Gateway deletion")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    delete_request = request_params.get('DeleteNatGatewayRequest', {})
    gw_id = delete_request.get('NatGatewayId', '')
    
    return [EventDetail(
        title=f"NAT Gateway {gw_id} deleted",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail.get('eventSource', ''),
        event_name=detail['eventName'],
        nat_gateway_id=gw_id
    )]


def handle_route_table_creation(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when a route table is created."""
    logger.info("Processing route table creation")
    
    detail = event['detail']
    response_elements = detail.get('responseElements', {})
    route_table = response_elements.get('routeTable', {})
    
    rt_id = route_table.get('routeTableId', '')
    vpc_id = route_table.get('vpcId', '')
    
    return [EventDetail(
        title=f"Route table {rt_id} created in VPC {vpc_id}",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail.get('eventSource', ''),
        event_name=detail['eventName'],
        vpc_id=vpc_id,
        route_table_id=rt_id
    )]


def handle_route_table_deletion(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when a route table is deleted."""
    logger.info("Processing route table deletion")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    rt_id = request_params.get('routeTableId', '')
    
    return [EventDetail(
        title=f"Route table {rt_id} deleted",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail.get('eventSource', ''),
        event_name=detail['eventName'],
        route_table_id=rt_id
    )]


def handle_network_acl_creation(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when a network ACL is created."""
    logger.info("Processing network ACL creation")
    
    detail = event['detail']
    response_elements = detail.get('responseElements', {})
    network_acl = response_elements.get('networkAcl', {})
    
    nacl_id = network_acl.get('networkAclId', '')
    vpc_id = network_acl.get('vpcId', '')
    
    return [EventDetail(
        title=f"Network ACL {nacl_id} created in VPC {vpc_id}",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail.get('eventSource', ''),
        event_name=detail['eventName'],
        vpc_id=vpc_id,
        nacl_id=nacl_id
    )]


def handle_network_acl_deletion(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when a network ACL is deleted."""
    logger.info("Processing network ACL deletion")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    nacl_id = request_params.get('networkAclId', '')
    
    return [EventDetail(
        title=f"Network ACL {nacl_id} deleted",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail.get('eventSource', ''),
        event_name=detail['eventName'],
        nacl_id=nacl_id
    )]


def handle_elastic_ip_allocation(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when an Elastic IP is allocated."""
    logger.info("Processing Elastic IP allocation")
    
    detail = event['detail']
    response_elements = detail.get('responseElements', {})
    alloc_id = response_elements.get('allocationId', '')
    
    return [EventDetail(
        title=f"Elastic IP {alloc_id} allocated",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail.get('eventSource', ''),
        event_name=detail['eventName'],
        allocation_id=alloc_id
    )]


def handle_elastic_ip_release(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when an Elastic IP is released."""
    logger.info("Processing Elastic IP release")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    alloc_id = request_params.get('allocationId', '')
    
    return [EventDetail(
        title=f"Elastic IP {alloc_id} released",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail.get('eventSource', ''),
        event_name=detail['eventName'],
        allocation_id=alloc_id
    )]


def handle_vpc_peering_creation(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when a VPC peering connection is created."""
    logger.info("Processing VPC peering creation")
    
    detail = event['detail']
    response_elements = detail.get('responseElements', {})
    vpc_peering = response_elements.get('vpcPeeringConnection', {})
    pcx_id = vpc_peering.get('vpcPeeringConnectionId', '')
    
    return [EventDetail(
        title=f"VPC peering connection {pcx_id} created",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail.get('eventSource', ''),
        event_name=detail['eventName'],
        resource_name=pcx_id
    )]


def handle_vpc_peering_deletion(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when a VPC peering connection is deleted."""
    logger.info("Processing VPC peering deletion")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    pcx_id = request_params.get('vpcPeeringConnectionId', '')
    
    return [EventDetail(
        title=f"VPC peering connection {pcx_id} deleted",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail.get('eventSource', ''),
        event_name=detail['eventName'],
        resource_name=pcx_id
    )]


def handle_vpc_endpoint_deletion(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when VPC endpoints are deleted."""
    logger.info("Processing VPC endpoint deletion")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    delete_request = request_params.get('DeleteVpcEndpointsRequest', {})
    vpc_endpoint_id = delete_request.get('VpcEndpointId', {})
    
    # Handle both string and dict formats
    if isinstance(vpc_endpoint_id, dict):
        ep_id = vpc_endpoint_id.get('content', '')
    else:
        ep_id = vpc_endpoint_id
    
    return [EventDetail(
        title=f"VPC endpoint {ep_id} deleted",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail.get('eventSource', ''),
        event_name=detail['eventName'],
        vpc_endpoint_id=ep_id
    )]
