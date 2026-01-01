#!/bin/bash

# CloudFormation deployment script for AWS Secrets Manager Backup
set -e

# Configuration
STACK_NAME="secrets-manager-backup"
TEMPLATE_FILE="cloudformation-template.yml"
LAMBDA_ZIP="lambda-deployment.zip"

# Parameters (update these values)
S3_BUCKET_NAME="secrets-manager-backup-$(date +%s)"
SCHEDULE_EXPRESSION="rate(1 day)"
ENVIRONMENT="production"
OWNER="DevOps Team"

echo "Starting AWS Secrets Manager Backup deployment..."

# Build Lambda package
echo "Building Lambda deployment package..."
./lambda_build.sh

# Deploy CloudFormation stack
echo "Deploying CloudFormation stack: $STACK_NAME"
aws cloudformation deploy \
  --template-file $TEMPLATE_FILE \
  --stack-name $STACK_NAME \
  --parameter-overrides \
    S3BucketName="$S3_BUCKET_NAME" \
    ScheduleExpression="$SCHEDULE_EXPRESSION" \
    Environment="$ENVIRONMENT" \
    Owner="$OWNER" \
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
echo "S3 Bucket: $S3_BUCKET_NAME"
echo "Schedule: $SCHEDULE_EXPRESSION"