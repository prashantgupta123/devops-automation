"""AWS Bedrock AgentCore Runtime - Agent Invocation Client"""

import json
import logging
from typing import Dict, Any

import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
REGION_NAME = 'us-east-1'
AGENT_RUNTIME_ARN = 'arn:aws:bedrock-agentcore:us-east-1:999999999999:runtime/hosted_agent_phmxx-dtrZCGFffv'
RUNTIME_SESSION_ID = 'dfmeoagmreaklgmrkleafremoigrmtesogmtrskhmtkrlshmt'  # Must be 33+ chars
QUALIFIER = "DEFAULT"


def invoke_agent(prompt: str) -> Dict[str, Any]:
    """Invoke the Bedrock AgentCore runtime with a given prompt.
    
    Args:
        prompt: The user prompt to send to the agent
        
    Returns:
        Dict containing the agent's response
        
    Raises:
        ClientError: If AWS API call fails
        Exception: If response processing fails
    """
    try:
        client = boto3.client('bedrock-agentcore', region_name=REGION_NAME)
        payload = json.dumps({"prompt": prompt})
        
        logger.info(f"Invoking agent with prompt length: {len(prompt)}")
        
        response = client.invoke_agent_runtime(
            agentRuntimeArn=AGENT_RUNTIME_ARN,
            runtimeSessionId=RUNTIME_SESSION_ID,
            payload=payload,
            qualifier=QUALIFIER
        )
        
        response_body = response['response'].read()
        response_data = json.loads(response_body)
        
        logger.info("Successfully received agent response")
        return response_data
        
    except ClientError as e:
        logger.error(f"AWS API error: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


def main():
    """Main function to demonstrate agent invocation."""
    try:
        prompt = "Explain machine learning in simple terms"
        response_data = invoke_agent(prompt)
        
        print("Agent Response:", response_data)
        
    except Exception as e:
        logger.error(f"Failed to invoke agent: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
