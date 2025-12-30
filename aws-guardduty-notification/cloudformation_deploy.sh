#!/bin/bash

# CloudFormation deployment script for GuardDuty Lambda
set -e

# Configuration
STACK_NAME="guardduty-notifications"
TEMPLATE_FILE="cloudformation-template.yaml"
LAMBDA_ZIP="lambda-deployment.zip"

# Parameters (update these values)
SNS_TOPIC_ARN=""
GOOGLE_CHAT_WEBHOOK=""
ENABLE_SNS="true"
ENABLE_EMAIL="false"
ENABLE_CHAT="true"

echo "Starting GuardDuty Lambda deployment..."

# Build Lambda package
echo "Building Lambda deployment package..."
./lambda_build.sh

# Deploy CloudFormation stack
echo "Deploying CloudFormation stack: $STACK_NAME"
aws cloudformation deploy \
  --template-file $TEMPLATE_FILE \
  --stack-name $STACK_NAME \
  --parameter-overrides \
    SNSTopicArn="$SNS_TOPIC_ARN" \
    GoogleChatWebhook="$GOOGLE_CHAT_WEBHOOK" \
    EnableSNS="$ENABLE_SNS" \
    EnableEmail="$ENABLE_EMAIL" \
    EnableChat="$ENABLE_CHAT" \
  --capabilities CAPABILITY_NAMED_IAM

# Get Lambda function name from stack outputs
echo "Getting Lambda function name..."
FUNCTION_NAME=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`LambdaFunctionArn`].OutputValue' \
  --output text | cut -d':' -f7)

# Update Lambda function code
echo "Updating Lambda function code: $FUNCTION_NAME"
aws lambda update-function-code \
  --function-name $FUNCTION_NAME \
  --zip-file fileb://$LAMBDA_ZIP

echo "Deployment completed successfully!"
echo "Lambda Function: $FUNCTION_NAME"