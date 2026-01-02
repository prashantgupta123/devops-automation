#!/bin/bash

# CloudFormation deployment script for Lambda
set -e

# Configuration
STACK_NAME="ecs-service-task-recycle"
TEMPLATE_FILE="cloudformation-template.yml"
LAMBDA_ZIP="lambda-deployment.zip"

# Parameters
ENVIRONMENT="production"
PROJECT="ecs-task-recycle"
OWNER="DevOps"
AWS_PROFILE="${AWS_PROFILE:-default}"

echo "Starting Lambda deployment..."

# Build Lambda package
echo "Building Lambda deployment package..."
./lambda_build.sh

# Deploy CloudFormation stack
echo "Deploying CloudFormation stack: $STACK_NAME"
aws cloudformation deploy \
  --template-file $TEMPLATE_FILE \
  --stack-name $STACK_NAME \
  --parameter-overrides \
    Environment=$ENVIRONMENT \
    Project=$PROJECT \
    Owner=$OWNER \
  --capabilities CAPABILITY_NAMED_IAM \
  --profile $AWS_PROFILE

# Get Lambda function name from stack outputs
echo "Getting Lambda function name..."
FUNCTION_NAME=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`LambdaFunctionName`].OutputValue' \
  --output text \
  --profile $AWS_PROFILE)

# Update Lambda function code
echo "Updating Lambda function code: $FUNCTION_NAME"
aws lambda update-function-code \
  --function-name $FUNCTION_NAME \
  --zip-file fileb://$LAMBDA_ZIP \
  --profile $AWS_PROFILE

echo "Deployment completed successfully!"
echo "Lambda Function: $FUNCTION_NAME"
echo ""
echo "Test the function with:"
echo "aws lambda invoke --function-name $FUNCTION_NAME --payload '{\"cluster_name\":\"my-cluster\",\"service_name\":\"my-service\",\"maintain_service_state\":true,\"wait_time\":30}' response.json --profile $AWS_PROFILE"