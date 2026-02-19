"""Event detail structure for AWS security monitoring."""

from typing import TypedDict, Optional


class EventDetail(TypedDict, total=False):
    """
    Event detail structure returned by handlers.
    
    Each handler returns a list of these dicts describing what was detected.
    The 'title' field is the human-readable summary used in email notifications.
    """
    # Human-readable summary of the violation (set by each handler)
    title: str
    
    # Common fields
    source_ip_address: str
    event_source: str
    event_name: str
    resource_name: str
    resource_value: str
    resource_id: str
    
    # Security group fields
    to_port: int
    from_port: int
    ip_range: str
    
    # IAM fields
    console_login_response: str
    mfa_used: str
    user_name: str
    key_generated_for: str
    key_deleted_for: str
    
    # VPC / network fields
    allocation_id: str
    nacl_id: str
    vpc_id: str
    subnet_id: str
    subnet_name: str
    nat_gateway_id: str
    route_table_id: str
    vpc_endpoint_id: str
    
    # Route53 fields
    hosted_zone_name: str
    hosted_zone_id: str
    record_name: str
    
    # Other resource fields
    backup_plan_id: str
    backup_vault_name: str
    repository_name: str
