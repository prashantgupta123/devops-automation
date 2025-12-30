"""AWS Session Management Module.

Provides flexible AWS authentication methods including:
- Profile-based authentication
- Assumed role authentication  
- Temporary credential authentication
- Access key authentication
- Default credential chain
"""

import boto3
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def get_aws_session(credentials: Dict[str, Any]) -> boto3.Session:
    """
    Create AWS session with flexible authentication methods.
    
    Args:
        credentials: Dictionary containing AWS credential information
        
    Returns:
        boto3.Session: Configured AWS session
        
    Raises:
        ValueError: If invalid credentials provided
        boto3.exceptions.Boto3Error: If session creation fails
    """
    region = credentials.get("region_name", "us-east-1")
    
    try:
        if credentials.get("profile_name"):
            logger.info("Creating AWS session with profile authentication")
            return boto3.Session(
                profile_name=credentials["profile_name"],
                region_name=region
            )
        
        elif credentials.get("role_arn"):
            logger.info("Creating AWS session with assumed role")
            return _create_assumed_role_session(credentials["role_arn"], region)
        
        elif credentials.get("session_token"):
            logger.info("Creating AWS session with temporary credentials")
            return boto3.Session(
                aws_access_key_id=credentials["access_key"],
                aws_secret_access_key=credentials["secret_key"],
                aws_session_token=credentials["session_token"],
                region_name=region
            )
        
        elif credentials.get("access_key"):
            logger.info("Creating AWS session with access keys")
            return boto3.Session(
                aws_access_key_id=credentials["access_key"],
                aws_secret_access_key=credentials["secret_key"],
                region_name=region
            )
        
        else:
            logger.info("Creating AWS session with default credentials")
            return boto3.Session(region_name=region)
            
    except Exception as e:
        logger.error(f"Failed to create AWS session: {str(e)}")
        raise


def _create_assumed_role_session(role_arn: str, region: str) -> boto3.Session:
    """Create session using assumed role credentials."""
    sts_client = boto3.client('sts', region_name=region)
    
    response = sts_client.assume_role(
        RoleArn=role_arn,
        RoleSessionName='GuardDutyNotificationSession',
        DurationSeconds=3600
    )
    
    credentials = response['Credentials']
    return boto3.Session(
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken'],
        region_name=region
    )
