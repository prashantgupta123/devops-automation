"""AWS Secrets Manager Backup Lambda Function.

Backups all AWS Secrets Manager secrets to S3 in JSON format daily.
Provides email notifications and comprehensive error handling.
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any
from botocore.exceptions import ClientError
from AWSSession import get_aws_session
from Notification import send_email

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_configuration() -> Dict[str, Any]:
    """Load configuration from input.json or environment variables."""
    try:
        with open('input.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("input.json not found, using environment variables")
        return {
            "awsCredentials": {
                "region_name": os.environ.get("AWS_REGION", "us-east-1")
            }
        }


def get_all_secrets(secrets_client) -> List[Dict[str, Any]]:
    """Retrieve all secrets from AWS Secrets Manager."""
    secrets = []
    paginator = secrets_client.get_paginator('list_secrets')
    
    for page in paginator.paginate():
        secrets.extend(page['SecretList'])
    
    logger.info(f"Found {len(secrets)} secrets to backup")
    return secrets


def get_secret_value(secrets_client, secret_name: str) -> str:
    """Retrieve secret value from AWS Secrets Manager."""
    try:
        response = secrets_client.get_secret_value(SecretId=secret_name)
        return response.get('SecretString', response.get('SecretBinary', ''))
    except ClientError as e:
        logger.error(f"Failed to retrieve secret {secret_name}: {e}")
        raise


def backup_secret_to_s3(s3_client, bucket_name: str, secret_name: str, secret_value: str) -> bool:
    """Backup secret to S3 with date-based organization."""
    try:
        current_date = datetime.now()
        sanitized_name = secret_name.replace('/', '-')
        
        # Create date-based path
        date_path = f"secrets-manager/{sanitized_name}/{current_date.year:04d}/{current_date.month:02d}/{current_date.day:02d}/{sanitized_name}.json"
        latest_path = f"secrets-manager/{sanitized_name}/latest.json"
        
        # Upload to both paths
        s3_client.put_object(
            Bucket=bucket_name,
            Key=date_path,
            Body=secret_value,
            ContentType='application/json'
        )
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key=latest_path,
            Body=secret_value,
            ContentType='application/json'
        )
        
        logger.info(f"Successfully backed up secret: {secret_name}")
        return True
        
    except ClientError as e:
        logger.error(f"Failed to backup secret {secret_name} to S3: {e}")
        return False


def send_notification(config: Dict[str, Any], success_count: int, total_count: int, failed_secrets: List[str]) -> None:
    """Send email notification about backup status."""
    if not config.get('smtpCredentials') or not config.get('emailNotification'):
        logger.info("Email notification not configured, skipping")
        return
    
    try:
        status = "SUCCESS" if not failed_secrets else "PARTIAL_FAILURE"
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        html_content = f"""
        <html>
        <body>
            <h2>AWS Secrets Manager Backup Report</h2>
            <p><strong>Date:</strong> {current_date}</p>
            <p><strong>Status:</strong> {status}</p>
            <p><strong>Total Secrets:</strong> {total_count}</p>
            <p><strong>Successfully Backed Up:</strong> {success_count}</p>
            <p><strong>Failed:</strong> {len(failed_secrets)}</p>
            
            {f'<h3>Failed Secrets:</h3><ul>{"".join([f"<li>{secret}</li>" for secret in failed_secrets])}</ul>' if failed_secrets else ''}
        </body>
        </html>
        """
        
        send_email(
            config['smtpCredentials'],
            config['emailNotification'],
            html_content
        )
        
        logger.info("Email notification sent successfully")
        
    except Exception as e:
        logger.error(f"Failed to send email notification: {e}")


def lambda_handler(event, context):
    """Main Lambda handler function."""
    logger.info("Starting AWS Secrets Manager backup process")
    
    try:
        # Load configuration
        config = load_configuration()
        bucket_name = os.environ.get('DESTINATION_S3_BUCKET')
        
        if not bucket_name:
            raise ValueError("DESTINATION_S3_BUCKET environment variable not set")
        
        # Create AWS session
        session = get_aws_session(config['awsCredentials'])
        secrets_client = session.client('secretsmanager')
        s3_client = session.client('s3')
        
        # Get all secrets
        secrets = get_all_secrets(secrets_client)
        
        if not secrets:
            logger.info("No secrets found to backup")
            return {'statusCode': 200, 'body': 'No secrets to backup'}
        
        # Backup each secret
        success_count = 0
        failed_secrets = []
        
        for secret in secrets:
            secret_name = secret['Name']
            try:
                secret_value = get_secret_value(secrets_client, secret_name)
                
                if backup_secret_to_s3(s3_client, bucket_name, secret_name, secret_value):
                    success_count += 1
                else:
                    failed_secrets.append(secret_name)
                    
            except Exception as e:
                logger.error(f"Error processing secret {secret_name}: {e}")
                failed_secrets.append(secret_name)
        
        # Send notification
        send_notification(config, success_count, len(secrets), failed_secrets)
        
        # Return result
        result = {
            'statusCode': 200 if not failed_secrets else 207,
            'body': {
                'message': 'Backup completed',
                'total_secrets': len(secrets),
                'successful_backups': success_count,
                'failed_backups': len(failed_secrets),
                'failed_secrets': failed_secrets
            }
        }
        
        logger.info(f"Backup process completed: {success_count}/{len(secrets)} successful")
        return result
        
    except Exception as e:
        logger.error(f"Lambda execution failed: {e}")
        return {
            'statusCode': 500,
            'body': {'error': str(e)}
        }
