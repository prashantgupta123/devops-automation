#!/bin/bash

# CloudFormation deployment script for Spot Interruption Lambda
set -e

# Configuration
STACK_NAME="spot-interruption"
TEMPLATE_FILE="cloudformation-template.yaml"
LAMBDA_ZIP="lambda-deployment.zip"

# Notification Settings
SNS_TOPIC_ARN=""
GOOGLE_CHAT_WEBHOOK=""
ENABLE_SNS="true"
ENABLE_EMAIL="false"
ENABLE_CHAT="true"

# Enhancement Settings
ENABLE_SLACK="false"
ENABLE_JIRA="false"
SLACK_WEBHOOK_URL=""
CRITICAL_SERVICES="web-service,api-service"
MAINTENANCE_START="02:00"
MAINTENANCE_END="04:00"
JIRA_URL=""
JIRA_USERNAME=""
JIRA_TOKEN=""
JIRA_PROJECT="INFRA"

echo "Starting Spot Interruption Lambda deployment..."

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
    EnableSlack="$ENABLE_SLACK" \
    EnableJira="$ENABLE_JIRA" \
    SlackWebhookUrl="$SLACK_WEBHOOK_URL" \
    CriticalServices="$CRITICAL_SERVICES" \
    MaintenanceStart="$MAINTENANCE_START" \
    MaintenanceEnd="$MAINTENANCE_END" \
    JiraUrl="$JIRA_URL" \
    JiraUsername="$JIRA_USERNAME" \
    JiraToken="$JIRA_TOKEN" \
    JiraProject="$JIRA_PROJECT" \
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