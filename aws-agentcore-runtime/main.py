"""AWS Bedrock AgentCore Runtime - AI Agent Implementation"""

import logging
from typing import Dict, Any

from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent
from strands.models import BedrockModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Bedrock model
bedrock_model = BedrockModel(
    model_id="anthropic.claude-3-haiku-20240307-v1:0",
    region_name="us-east-1",
)

# Initialize app and agent
app = BedrockAgentCoreApp()
agent = Agent(model=bedrock_model)


@app.entrypoint
def invoke(payload: Dict[str, Any]) -> Dict[str, str]:
    """AI agent entrypoint function.
    
    Args:
        payload: Input payload containing the user prompt
        
    Returns:
        Dict containing the agent's response
        
    Raises:
        Exception: If agent processing fails
    """
    try:
        user_message = payload.get("prompt", "Hello! How can I help you today?")
        logger.info(f"Processing request with prompt length: {len(user_message)}")
        
        result = agent(user_message)
        
        logger.info("Successfully processed agent request")
        return {"result": result.message}
        
    except Exception as e:
        logger.error(f"Agent processing failed: {str(e)}")
        return {"result": f"Error processing request: {str(e)}"}


if __name__ == "__main__":
    logger.info("Starting AWS Bedrock AgentCore Runtime")
    app.run()
