"""Settings management for AWS security monitoring."""

import boto3
import json
import os
from typing import Dict, Any, Optional
from utils.logger import setup_logger
from core.exceptions import ConfigurationError

logger = setup_logger(__name__)


class Config:
    """Configuration manager for security monitoring."""
    
    def __init__(self):
        """Initialize configuration from environment and Secrets Manager."""
        self.account_name = os.environ.get('ACCOUNTNAME', 'Unknown')
        self.layer_version = os.environ.get('LAYERVERSION', '1')
        self.email_ids = os.environ.get('EMAILIDS', '')
        self.secret_name = os.environ.get('SECRETNAME', '')
        self.secret_region = os.environ.get('SECRETREGION', 'us-east-1')
        
        # Load secrets
        self._secrets = self._load_secrets()
        
        self.ses_source_email = self._secrets.get('EMAIL_FROM', '')
        self.ses_region = self._secrets.get('SES_REGION', 'us-east-1')
        self.ses_access_key = self._secrets.get('ACCESS_KEY', 'NA')
        self.ses_secret_key = self._secrets.get('ACCESS_SECRET_KEY', 'NA')
        
        # Validate configuration
        self._validate()
    
    def _load_secrets(self) -> Dict[str, Any]:
        """
        Load secrets from AWS Secrets Manager.
        
        Returns:
            Dictionary of secrets
        
        Raises:
            ConfigurationError: If secrets cannot be retrieved
        """
        if not self.secret_name:
            logger.warning("No secret name configured, using empty secrets")
            return {}
        
        try:
            client = boto3.client(
                service_name='secretsmanager',
                region_name=self.secret_region
            )
            
            response = client.get_secret_value(SecretId=self.secret_name)
            secret_string = response.get('SecretString', '{}')
            
            secrets = json.loads(secret_string)
            logger.info(f"Successfully loaded secrets from {self.secret_name}")
            return secrets
            
        except Exception as e:
            logger.error(f"Error retrieving secret {self.secret_name}: {e}")
            raise ConfigurationError(f"Failed to load secrets: {e}") from e
    
    def _validate(self) -> None:
        """
        Validate required configuration values.
        
        Raises:
            ConfigurationError: If required configuration is missing
        """
        if not self.ses_source_email:
            raise ConfigurationError("SES source email (EMAIL_FROM) is required")
        
        if not self.email_ids:
            logger.warning("No email recipients configured (EMAILIDS)")


# Singleton config instance — loaded once at module import time
config: Optional[Config] = None

def get_config() -> Config:
    """Get or create the singleton config instance."""
    global config
    if config is None:
        config = Config()
    return config
