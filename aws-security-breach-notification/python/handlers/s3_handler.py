"""S3 event handlers for detecting public bucket access."""

from typing import Dict, Any, List
from core.event_types import EventDetail
from utils.logger import setup_logger

logger = setup_logger(__name__)


def handle_s3_public_access(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """
    Detect S3 buckets being made public via ACL or public access block changes.
    Covers: PutBucketPublicAccessBlock, PutBucketAcl
    """
    logger.info("Processing S3 public access event")

    detail = event['detail']
    event_name = detail['eventName']
    request_params = detail.get('requestParameters', {})
    bucket_name = request_params.get('bucketName', 'Unknown')
    ip = detail.get("sourceIPAddress", "")

    if event_name == 'PutBucketAcl':
        acl = request_params.get('x-amz-acl', [])
        if set(acl) & {'public-read', 'public-read-write'}:
            return [EventDetail(
                title=f"S3 bucket {bucket_name} ACL set to {', '.join(acl)}",
                source_ip_address=ip,
                resource_name=bucket_name
            )]

    elif event_name == 'PutBucketPublicAccessBlock':
        config = request_params.get('PublicAccessBlockConfiguration', {})
        if not all([
            config.get('RestrictPublicBuckets'),
            config.get('BlockPublicPolicy'),
            config.get('BlockPublicAcls'),
            config.get('IgnorePublicAcls')
        ]):
            return [EventDetail(
                title=f"S3 bucket {bucket_name} public access block weakened",
                source_ip_address=ip,
                resource_name=bucket_name
            )]

    return []
