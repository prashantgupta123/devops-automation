"""Security group event handlers for detecting public access rules."""

from typing import Dict, Any, List, Optional
from core.event_types import EventDetail
from core.constants import INGRESS_WHITELIST_PORTS, EGRESS_WHITELIST_PORTS
from utils.logger import setup_logger

logger = setup_logger(__name__)


def handle_security_group_ingress(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Detect security group rules that allow public inbound access (0.0.0.0/0 or ::/0)."""
    return _handle_security_group_rules(event, INGRESS_WHITELIST_PORTS, "Inbound")


def handle_security_group_egress(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Detect security group rules that allow public outbound access (0.0.0.0/0 or ::/0)."""
    return _handle_security_group_rules(event, EGRESS_WHITELIST_PORTS, "Outbound")


def _handle_security_group_rules(
    event: Dict[str, Any],
    whitelist_ports: List[int],
    direction: str
) -> List[EventDetail]:
    """Process security group rule changes and detect public access violations."""
    logger.info(f"Processing security group {direction.lower()} event")

    try:
        request_params = event['detail']['requestParameters']
        sg_rules = request_params.get('ipPermissions', {}).get('items', [])
    except KeyError:
        logger.warning("Security group rules not found in event")
        return []

    sg_id = request_params.get('groupId') or request_params.get('groupName')
    if not sg_id:
        logger.warning("No security group identifier found")
        return []

    violations = []
    for rule in sg_rules:
        violations.extend(_check_ipv4_violations(sg_id, rule, whitelist_ports, direction))
        violations.extend(_check_ipv6_violations(sg_id, rule, whitelist_ports, direction))

    logger.info(f"Found {len(violations)} violations")
    return violations


def _check_ipv4_violations(sg_id: str, rule: Dict, whitelist: List[int], direction: str) -> List[EventDetail]:
    violations = []
    for ip_range in rule.get('ipRanges', {}).get('items', []):
        if ip_range.get('cidrIp') == '0.0.0.0/0':
            v = _create_violation(sg_id, rule, '0.0.0.0/0', whitelist, direction)
            if v:
                violations.append(v)
    return violations


def _check_ipv6_violations(sg_id: str, rule: Dict, whitelist: List[int], direction: str) -> List[EventDetail]:
    violations = []
    for ipv6_range in rule.get('ipv6Ranges', {}).get('items', []):
        if ipv6_range.get('cidrIpv6') == '::/0':
            v = _create_violation(sg_id, rule, '::/0', whitelist, direction)
            if v:
                violations.append(v)
    return violations


def _create_violation(
    sg_id: str, rule: Dict, cidr: str, whitelist: List[int], direction: str
) -> Optional[EventDetail]:
    """Create a violation if the port is not whitelisted."""
    if rule.get("ipProtocol") == '-1':
        to_port, from_port = 65535, 0
    else:
        to_port = rule.get("toPort", 0)
        from_port = rule.get("fromPort", 0)

    if to_port in whitelist:
        return None

    return EventDetail(
        title=f"SG {direction} Port {from_port}-{to_port} opened for {cidr} in {sg_id}",
        resource_id=sg_id,
        to_port=to_port,
        from_port=from_port,
        ip_range=cidr
    )
