#!/bin/bash

# CloudFormation deployment script for EC2 Backup Compliance Checker
set -e

# Configuration
STACK_NAME="ec2-backup-compliance-stack"
TEMPLATE_FILE="cloudformation-template.yaml"
REGION="ap-south-1"

# Parameters (modify as needed)
LAMBDA_FUNCTION_NAME="ec2-backup-compliance-checker"
SMTP_SECRET_NAME="ses-smtp-user/example-Projects"
NOTIFICATION_EMAIL="prashantgupta@cloudplatform.com"
SUBJECT_PREFIX="MyProject"
SCHEDULE_EXPRESSION="rate(1 day)"

echo "Deploying EC2 Backup Compliance Checker..."

# Create deployment package
echo "Creating Lambda deployment package..."
./deploy.sh

# Deploy CloudFormation stack
echo "Deploying CloudFormation stack: $STACK_NAME"
aws cloudformation deploy \
    --template-file $TEMPLATE_FILE \
    --stack-name $STACK_NAME \
    --parameter-overrides \
        LambdaFunctionName=$LAMBDA_FUNCTION_NAME \
        SMTPSecretName=$SMTP_SECRET_NAME \
        NotificationEmail=$NOTIFICATION_EMAIL \
        SubjectPrefix=$SUBJECT_PREFIX \
        ScheduleExpression="$SCHEDULE_EXPRESSION" \
    --capabilities CAPABILITY_NAMED_IAM \
    --region $REGION

# Update Lambda function code
echo "Updating Lambda function code..."
aws lambda update-function-code \
    --function-name $LAMBDA_FUNCTION_NAME \
    --zip-file fileb://lambda-deployment.zip \
    --region $REGION

echo "Deployment completed successfully!"
echo "Stack Name: $STACK_NAME"
echo "Lambda Function: $LAMBDA_FUNCTION_NAME"
echo "Schedule: $SCHEDULE_EXPRESSION"