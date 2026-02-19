"""IAM event handlers for access keys, console login, and user management."""

from typing import Dict, Any, List
from core.event_types import EventDetail
from utils.logger import setup_logger

logger = setup_logger(__name__)


def handle_access_key_creation(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when a new IAM access key is created."""
    logger.info("Processing access key creation")
    user_name = (event['detail']
                 .get('responseElements', {})
                 .get('accessKey', {})
                 .get('userName', 'Unknown'))
    return [EventDetail(
        title=f"Access key created for user {user_name}",
        key_generated_for=user_name
    )]


def handle_access_key_deletion(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when an IAM access key is deleted."""
    logger.info("Processing access key deletion")
    user_name = (event['detail']
                 .get('requestParameters', {})
                 .get('userName', 'Unknown'))
    return [EventDetail(
        title=f"Access key deleted for user {user_name}",
        key_deleted_for=user_name
    )]


def handle_console_login(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """
    Alert on suspicious console logins:
    - Root user login
    - Login without MFA
    - Failed login attempts
    Skips AssumedRole sessions (they don't use MFA directly).
    """
    logger.info("Processing console login")

    detail = event['detail']
    mfa_used = detail.get("additionalEventData", {}).get("MFAUsed", "No")
    user_type = detail['userIdentity'].get('type', 'Unknown')
    login_response = detail.get("responseElements", {}).get("ConsoleLogin", "Unknown")
    user_name = detail['userIdentity'].get('userName', user_type)
    ip = detail.get("sourceIPAddress", "")

    # Only alert if: failed login, root user, or no MFA (excluding AssumedRole)
    if login_response != "Failure" and (mfa_used == "No" or user_type == "Root") and user_type != "AssumedRole":
        # Build a descriptive title
        if user_type == "Root":
            title = f"Root user console login, MFA: {mfa_used}, IP: {ip}"
        elif mfa_used == "No":
            title = f"Console login without MFA for {user_name}, IP: {ip}"
        else:
            title = f"Console login for {user_name}, MFA: {mfa_used}, IP: {ip}"

        return [EventDetail(
            title=title,
            source_ip_address=ip,
            console_login_response=login_response,
            mfa_used=mfa_used,
            user_name=user_name
        )]

    return []


def handle_iam_user_create(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when a new IAM user is created."""
    logger.info("Processing IAM user creation")
    detail = event['detail']
    user_name = detail.get('requestParameters', {}).get('userName', 'Unknown')
    return [EventDetail(
        title=f"IAM user {user_name} created",
        source_ip_address=detail["sourceIPAddress"],
        event_source=detail['eventSource'],
        event_name=detail['eventName'],
        resource_name=user_name
    )]


def handle_iam_user_delete(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """Alert when an IAM user is deleted."""
    logger.info("Processing IAM user deletion")
    detail = event['detail']
    user_name = detail.get('requestParameters', {}).get('userName', 'Unknown')
    return [EventDetail(
        title=f"IAM user {user_name} deleted",
        source_ip_address=detail["sourceIPAddress"],
        event_source=detail['eventSource'],
        event_name=detail['eventName'],
        resource_name=user_name
    )]
