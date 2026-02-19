"""AWS Backup event handlers for backup plan and vault deletion."""

from typing import Dict, Any, List
from core.event_types import EventDetail
from utils.logger import setup_logger

logger = setup_logger(__name__)


def handle_backup_plan_deletion(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when a backup plan is deleted."""
    logger.info("Processing backup plan deletion")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    plan_id = request_params.get('backupPlanId', '')
    
    return [EventDetail(
        title=f"Backup plan {plan_id} deleted",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail.get('eventSource', ''),
        event_name=detail['eventName'],
        backup_plan_id=plan_id
    )]


def handle_backup_vault_deletion(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when a backup vault is deleted."""
    logger.info("Processing backup vault deletion")
    
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    vault_name = request_params.get('backupVaultName', '')
    
    return [EventDetail(
        title=f"Backup vault {vault_name} deleted",
        source_ip_address=detail.get("sourceIPAddress", ""),
        event_source=detail.get('eventSource', ''),
        event_name=detail['eventName'],
        backup_vault_name=vault_name
    )]
