#!/bin/bash

# AWS News Lambda Deployment Script
set -e

# Configuration
FUNCTION_NAME="aws-news-notifier"
RUNTIME="python3.14"
HANDLER="lambda_function.lambda_handler"
MEMORY_SIZE=128
TIMEOUT=30
SCHEDULE_EXPRESSION="cron(0 9 * * ? *)"
RULE_NAME="aws-news-daily"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 AWS News Lambda Deployment Script${NC}"
echo "=================================="

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not configured. Please run 'aws configure' first.${NC}"
    exit 1
fi

# Get AWS account info
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=$(aws configure get region)

echo -e "${GREEN}✅ AWS Account: ${ACCOUNT_ID}${NC}"
echo -e "${GREEN}✅ Region: ${REGION}${NC}"

# Check for required environment variables
if [ -z "$WEBHOOK_URL" ]; then
    echo -e "${YELLOW}⚠️  WEBHOOK_URL not set. Please provide your Google Chat webhook URL:${NC}"
    read -p "Webhook URL: " WEBHOOK_URL
    if [ -z "$WEBHOOK_URL" ]; then
        echo -e "${RED}❌ Webhook URL is required${NC}"
        exit 1
    fi
fi

# Build deployment package
echo -e "${YELLOW}📦 Building deployment package...${NC}"
./build.sh

if [ ! -f "lambda-deployment.zip" ]; then
    echo -e "${RED}❌ Deployment package not found${NC}"
    exit 1
fi

# Check if IAM role exists, create if not
ROLE_NAME="aws-news-lambda-role"
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

if ! aws iam get-role --role-name $ROLE_NAME &> /dev/null; then
    echo -e "${YELLOW}🔐 Creating IAM role...${NC}"
    
    # Create trust policy
    cat > trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

    aws iam create-role \
        --role-name $ROLE_NAME \
        --assume-role-policy-document file://trust-policy.json

    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

    rm trust-policy.json
    
    echo -e "${GREEN}✅ IAM role created${NC}"
    sleep 10  # Wait for role propagation
else
    echo -e "${GREEN}✅ IAM role exists${NC}"
fi

# Deploy or update Lambda function
if aws lambda get-function --function-name $FUNCTION_NAME &> /dev/null; then
    echo -e "${YELLOW}🔄 Updating existing Lambda function...${NC}"
    
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://lambda-deployment.zip

    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --environment Variables="{WEBHOOK_URL=$WEBHOOK_URL}"
        
    echo -e "${GREEN}✅ Lambda function updated${NC}"
else
    echo -e "${YELLOW}🆕 Creating new Lambda function...${NC}"
    
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime $RUNTIME \
        --role $ROLE_ARN \
        --handler $HANDLER \
        --zip-file fileb://lambda-deployment.zip \
        --memory-size $MEMORY_SIZE \
        --timeout $TIMEOUT \
        --environment Variables="{WEBHOOK_URL=$WEBHOOK_URL}"
        
    echo -e "${GREEN}✅ Lambda function created${NC}"
fi

# Create or update EventBridge rule
if aws events describe-rule --name $RULE_NAME &> /dev/null; then
    echo -e "${GREEN}✅ EventBridge rule exists${NC}"
else
    echo -e "${YELLOW}⏰ Creating EventBridge rule...${NC}"
    
    aws events put-rule \
        --name $RULE_NAME \
        --schedule-expression "$SCHEDULE_EXPRESSION" \
        --description "Daily trigger for AWS news notifications"

    # Add Lambda as target
    aws events put-targets \
        --rule $RULE_NAME \
        --targets "Id"="1","Arn"="arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${FUNCTION_NAME}"

    # Grant permission for EventBridge to invoke Lambda
    aws lambda add-permission \
        --function-name $FUNCTION_NAME \
        --statement-id $RULE_NAME \
        --action lambda:InvokeFunction \
        --principal events.amazonaws.com \
        --source-arn "arn:aws:events:${REGION}:${ACCOUNT_ID}:rule/${RULE_NAME}" \
        &> /dev/null || true

    echo -e "${GREEN}✅ EventBridge rule created${NC}"
fi

# Test the function
echo -e "${YELLOW}🧪 Testing Lambda function...${NC}"
aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --payload '{}' \
    test-response.json

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Test successful${NC}"
    cat test-response.json
    rm test-response.json
else
    echo -e "${RED}❌ Test failed${NC}"
fi

# Clean up
rm -f lambda-deployment.zip

echo ""
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo "=================================="
echo -e "Function Name: ${FUNCTION_NAME}"
echo -e "Schedule: Daily at 9 AM UTC"
echo -e "Logs: https://console.aws.amazon.com/cloudwatch/home?region=${REGION}#logsV2:log-groups/log-group/%2Faws%2Flambda%2F${FUNCTION_NAME}"
echo ""
echo -e "${YELLOW}💡 Next steps:${NC}"
echo "1. Check CloudWatch logs for execution details"
echo "2. Verify Google Chat receives test message"
echo "3. Monitor daily executions"