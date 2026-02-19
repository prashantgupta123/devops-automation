# Quick Reference Guide

## Common Operations

### Deploy New Version

```bash
# 1. Package layer
./deploy.sh

# 2. Note the layer version from output
# Example: Version: 2

# 3. Update CloudFormation stack
aws cloudformation update-stack \
  --stack-name aws-security-monitoring \
  --template-body file://AWS-Generic-Security-Template.yml \
  --parameters \
    ParameterKey=LambdaLayerVersion,ParameterValue=2 \
    ParameterKey=AccountName,UsePreviousValue=true \
    ParameterKey=EmailIds,UsePreviousValue=true \
  --capabilities CAPABILITY_NAMED_IAM
```

### View Logs

```bash
# Tail logs in real-time
aws logs tail /aws/lambda/AWS-Generic-Security-us-east-1 --follow

# View last 100 lines
aws logs tail /aws/lambda/AWS-Generic-Security-us-east-1 --since 1h

# Search for specific event
aws logs filter-log-events \
  --log-group-name /aws/lambda/AWS-Generic-Security-us-east-1 \
  --filter-pattern "RunInstances" \
  --start-time $(date -u -d '1 hour ago' +%s)000
```

### Test Handler Locally

```python
# test_handler.py
import json
from handlers.ec2_handler import handle_ec2_public_instance

# Load test event
with open('test_events/run_instances.json') as f:
    event = json.load(f)

# Test handler
result = handle_ec2_public_instance(event, None)
print(f"Violations found: {len(result)}")
for violation in result:
    print(f"  - {violation['title']}")
```

### Update Email Recipients

```bash
# Update CloudFormation parameter
aws cloudformation update-stack \
  --stack-name aws-security-monitoring \
  --use-previous-template \
  --parameters \
    ParameterKey=EmailIds,ParameterValue="new@example.com,another@example.com" \
    ParameterKey=AccountName,UsePreviousValue=true \
    ParameterKey=LambdaLayerVersion,UsePreviousValue=true \
  --capabilities CAPABILITY_NAMED_IAM
```

### Update SES Configuration

```bash
# Update Secrets Manager secret
aws secretsmanager update-secret \
  --secret-id AWS-Generic-Security-us-east-1 \
  --secret-string '{
    "EMAIL_FROM": "new-sender@example.com",
    "SES_REGION": "us-east-1",
    "ACCESS_KEY": "NA",
    "ACCESS_SECRET_KEY": "NA"
  }'
```

### Manually Trigger Test Event

```bash
# Create test event file
cat > test_event.json << 'EOF'
{
  "version": "0",
  "id": "test-123",
  "detail-type": "AWS API Call via CloudTrail",
  "source": "aws.ec2",
  "time": "2024-01-01T00:00:00Z",
  "region": "us-east-1",
  "detail": {
    "eventName": "RunInstances",
    "eventSource": "ec2.amazonaws.com",
    "sourceIPAddress": "1.2.3.4",
    "awsRegion": "us-east-1",
    "userIdentity": {
      "type": "IAMUser",
      "accountId": "123456789012",
      "arn": "arn:aws:iam::123456789012:user/test"
    },
    "requestParameters": {},
    "responseElements": {
      "instancesSet": {
        "items": [
          {
            "instanceId": "i-1234567890abcdef0",
            "subnetId": "subnet-12345678"
          }
        ]
      }
    }
  }
}
EOF

# Invoke Lambda directly
aws lambda invoke \
  --function-name AWS-Generic-Security-us-east-1 \
  --payload file://test_event.json \
  response.json

# View response
cat response.json
```

### Check Lambda Configuration

```bash
# Get function details
aws lambda get-function \
  --function-name AWS-Generic-Security-us-east-1

# Get environment variables
aws lambda get-function-configuration \
  --function-name AWS-Generic-Security-us-east-1 \
  --query 'Environment.Variables'
```

### Monitor Lambda Metrics

```bash
# Get invocation count (last hour)
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=AWS-Generic-Security-us-east-1 \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum

# Get error count (last hour)
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=AWS-Generic-Security-us-east-1 \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum
```

### Verify EventBridge Rule

```bash
# List rules
aws events list-rules --name-prefix AWS-Generic-Security

# Get rule details
aws events describe-rule \
  --name AWS-Generic-Security-events-us-east-1

# List targets
aws events list-targets-by-rule \
  --rule AWS-Generic-Security-events-us-east-1
```

### Add New Event to Monitor

```bash
# 1. Add handler in appropriate file
# Example: python/handlers/ec2_handler.py

# 2. Register in main.py
# register_handler('NewEventName')(handle_new_event)

# 3. Update CloudFormation template
# Add to eventName list in EventBridge rule

# 4. Deploy
./deploy.sh

# 5. Update stack
aws cloudformation update-stack \
  --stack-name aws-security-monitoring \
  --template-body file://AWS-Generic-Security-Template.yml \
  --parameters \
    ParameterKey=LambdaLayerVersion,ParameterValue=NEW_VERSION \
    ParameterKey=AccountName,UsePreviousValue=true \
    ParameterKey=EmailIds,UsePreviousValue=true \
  --capabilities CAPABILITY_NAMED_IAM
```

### Troubleshooting Commands

```bash
# Check if Lambda has correct layer
aws lambda get-function-configuration \
  --function-name AWS-Generic-Security-us-east-1 \
  --query 'Layers[*].Arn'

# Check Lambda execution role permissions
aws lambda get-function \
  --function-name AWS-Generic-Security-us-east-1 \
  --query 'Configuration.Role'

# Verify SES sender identity
aws ses get-identity-verification-attributes \
  --identities alerts@example.com

# Check Secrets Manager secret
aws secretsmanager get-secret-value \
  --secret-id AWS-Generic-Security-us-east-1 \
  --query 'SecretString' \
  --output text | jq .

# Test SES sending
aws ses send-email \
  --from alerts@example.com \
  --to test@example.com \
  --subject "Test Email" \
  --text "This is a test"
```

### Cleanup/Deletion

```bash
# Delete CloudFormation stack (keeps layer)
aws cloudformation delete-stack \
  --stack-name aws-security-monitoring

# Wait for deletion
aws cloudformation wait stack-delete-complete \
  --stack-name aws-security-monitoring

# Delete Lambda layer versions (optional)
aws lambda delete-layer-version \
  --layer-name AWS-Generic-Security \
  --version-number 1
```

## File Locations

| Component | Location |
|-----------|----------|
| Lambda Layer Code | `python/` |
| Handler Functions | `python/handlers/` |
| Configuration | `python/core/settings.py` |
| Constants | `python/core/constants.py` |
| CloudFormation | `AWS-Generic-Security-Template.yml` |
| Deployment Script | `deploy.sh` |
| Documentation | `*.md` files |

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `ACCOUNTNAME` | Account identifier | `Production-Account` |
| `EMAILIDS` | Comma-separated recipients | `admin@example.com,security@example.com` |
| `LAYERVERSION` | Lambda layer version | `1` |
| `SECRETNAME` | Secrets Manager secret name | `AWS-Generic-Security-us-east-1` |
| `SECRETREGION` | AWS region for Secrets Manager | `us-east-1` |

## Secrets Manager Format

```json
{
  "EMAIL_FROM": "alerts@example.com",
  "SES_REGION": "us-east-1",
  "ACCESS_KEY": "NA",
  "ACCESS_SECRET_KEY": "NA"
}
```

Note: Set `ACCESS_KEY` and `ACCESS_SECRET_KEY` only if using SMTP credentials. Otherwise, use IAM role permissions.

## Common Event Names

| Service | Event Name | Handler |
|---------|------------|---------|
| EC2 | `RunInstances` | `handle_ec2_public_instance` |
| EC2 | `CreateSecurityGroup` | `handle_ec2_public_security_group` |
| EC2 | `AuthorizeSecurityGroupIngress` | `handle_security_group_ingress` |
| RDS | `CreateDBInstance` | `handle_rds_public_instance` |
| S3 | `PutBucketAcl` | `handle_s3_public_access` |
| IAM | `CreateAccessKey` | `handle_access_key_creation` |
| IAM | `ConsoleLogin` | `handle_console_login` |
| CloudTrail | `StopLogging` | `handle_cloudtrail_event` |
| VPC | `CreateVpc` | `handle_resource_creation` |
| VPC | `DeleteVpc` | `handle_resource_deletion` |

## Useful CloudWatch Insights Queries

### Find all violations in last hour
```
fields @timestamp, @message
| filter @message like /violation/
| sort @timestamp desc
| limit 100
```

### Count violations by event type
```
fields @timestamp, detail.eventName as event
| filter @message like /violation/
| stats count() by event
```

### Find errors
```
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
```

### Track email sending
```
fields @timestamp, @message
| filter @message like /Email sent/
| stats count()
```
