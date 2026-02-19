# AWS Security Breach Notification

Automated security monitoring solution that detects and alerts on suspicious AWS activities in real-time using CloudWatch Events and Lambda.

## Overview

This solution monitors critical AWS API calls via CloudTrail and sends immediate email notifications when security-sensitive events occur, such as:

- **IAM Security**: Access key creation/deletion, console login without MFA, root user access
- **Network Security**: Public security groups, public EC2/RDS instances, public subnets
- **Resource Exposure**: Public S3 buckets, public snapshots, public AMIs
- **Infrastructure Changes**: VPC/subnet/NAT gateway creation/deletion, route table modifications
- **Service Disruptions**: CloudTrail deletion, backup plan/vault deletion, secret deletion

## Architecture

```
CloudTrail Events → EventBridge Rule → Lambda Function → SES Email Notification
                                            ↓
                                    Lambda Layer (Python)
                                            ↓
                                    Secrets Manager (SMTP Config)
```

## Features

✅ **Real-time Detection**: Immediate alerts on security events  
✅ **Comprehensive Coverage**: 40+ AWS event types monitored  
✅ **Customizable**: Easy to add new handlers and modify rules  
✅ **Production-Ready**: Proper error handling, logging, and type safety  
✅ **Scalable**: Serverless architecture scales automatically  
✅ **Cost-Effective**: ~$1-5/month for typical usage  

## Code Structure

```
python/
├── main.py                         # Lambda entry point & handler registry
├── requirements.txt                # Python dependencies
├── core/
│   ├── base_handler.py             # Abstract base class for handlers
│   ├── constants.py                # Whitelisted ports, public CIDRs
│   ├── enums.py                    # EventType enum (EVENT, INFO)
│   ├── event_types.py              # EventDetail TypedDict definition
│   ├── exceptions.py               # Custom exception classes
│   └── settings.py                 # Config from env vars & Secrets Manager
├── handlers/                       # One file per AWS service
│   ├── alb_handler.py              # Application Load Balancer
│   ├── backup_handler.py           # AWS Backup plans & vaults
│   ├── cloudtrail_handler.py       # Trail deletion / logging stopped
│   ├── ec2_handler.py              # Public instances, snapshots, AMIs, SGs
│   ├── ecr_handler.py              # Elastic Container Registry
│   ├── iam_handler.py              # Access keys, console login, user mgmt
│   ├── lambda_handler.py           # Function create/update tracking
│   ├── rds_handler.py              # Public RDS instances & snapshots
│   ├── route53_handler.py          # DNS hosted zones & records
│   ├── s3_handler.py               # Bucket public access
│   ├── secretsmanager_handler.py   # Secret deletion
│   ├── security_group_handler.py   # Ingress/egress public rules
│   └── vpc_handler.py              # VPC, subnet, NAT, route tables, etc.
├── services/
│   └── notification_service.py     # HTML email generation & SES sending
└── utils/
    ├── aws_helpers.py              # Shared AWS checks (public subnet, SG)
    └── logger.py                   # Logging setup
```

## Quick Start

### Prerequisites

- AWS Account with CloudTrail enabled
- SES verified email addresses (sender and recipients)
- IAM permissions for Lambda, EventBridge, Secrets Manager, and SES
- Python 3.14 runtime support
- AWS CLI configured

### Deployment

#### Step 1: Prepare Lambda Layer

```bash
cd python
zip -r ../layer.zip *
cd ..
```

Or use the deployment script:

```bash
chmod +x deploy.sh
./deploy.sh
```

#### Step 2: Deploy CloudFormation Stack

```bash
aws cloudformation create-stack \
  --stack-name aws-security-monitoring \
  --template-body file://AWS-Generic-Security-Template.yml \
  --parameters \
    ParameterKey=AccountName,ParameterValue="YourAccountName" \
    ParameterKey=EmailIds,ParameterValue="security@example.com,admin@example.com" \
    ParameterKey=LambdaLayerVersion,ParameterValue="1" \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

#### Step 3: Configure SES Credentials

Update the Secrets Manager secret created by CloudFormation:

```bash
aws secretsmanager update-secret \
  --secret-id AWS-Generic-Security-us-east-1 \
  --secret-string '{
    "EMAIL_FROM": "alerts@yourdomain.com",
    "SES_REGION": "us-east-1",
    "ACCESS_KEY": "NA",
    "ACCESS_SECRET_KEY": "NA"
  }'
```

Note: If using SES in a different region or with SMTP credentials, update ACCESS_KEY and ACCESS_SECRET_KEY.

## Adding a New Handler

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed instructions.

Quick example:

```python
# 1. Create handler function
def handle_new_event(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    detail = event['detail']
    # Check for violations
    if is_violation(detail):
        return [EventDetail(
            title="Violation detected",
            resource_name="resource-id"
        )]
    return []

# 2. Register in main.py
register_handler('EventName')(handle_new_event)

# 3. Add to CloudFormation template
# detail:
#   eventName:
#     - EventName
```

## Configuration

### Environment Variables

Set via CloudFormation parameters:

- `ACCOUNTNAME`: Account identifier for email subject
- `EMAILIDS`: Comma-separated list of recipient emails
- `LAYERVERSION`: Lambda layer version number
- `SECRETNAME`: Secrets Manager secret name
- `SECRETREGION`: AWS region for Secrets Manager

### Whitelisted Ports

Modify `python/core/constants.py`:

```python
INGRESS_WHITELIST_PORTS = [80, 443, 53]  # HTTP, HTTPS, DNS
EGRESS_WHITELIST_PORTS = [80, 443, 587]  # HTTP, HTTPS, SMTP
```

## Monitoring

### CloudWatch Logs

```bash
# Tail logs in real-time
aws logs tail /aws/lambda/AWS-Generic-Security-us-east-1 --follow

# Search for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/AWS-Generic-Security-us-east-1 \
  --filter-pattern "ERROR"
```

### Metrics

Monitor in CloudWatch:
- Lambda invocations
- Lambda errors
- Lambda duration
- SES send statistics

## Troubleshooting

### No Emails Received

1. Verify SES sender/recipient addresses are verified
2. Check Secrets Manager configuration
3. Review Lambda execution logs for errors
4. Ensure Lambda has SES permissions

### Handler Not Triggered

1. Verify EventBridge rule is enabled
2. Check event name matches exactly in CloudFormation
3. Review CloudTrail to confirm event is being logged
4. Check Lambda permissions

### False Positives

1. Adjust whitelisted ports in `constants.py`
2. Modify handler logic for your specific use case
3. Add exclusion rules in handlers

## Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design and architecture patterns
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Guide for adding new event handlers
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Common operations and commands
- **[DOCS.md](DOCS.md)** - Documentation guide and navigation

## Security Best Practices

- ✅ Least privilege IAM roles
- ✅ Secrets stored in Secrets Manager
- ✅ Encryption at rest and in transit
- ✅ CloudWatch Logs for audit trail
- ✅ No hardcoded credentials

## Cost Estimate

- **Lambda**: Free tier covers 1M requests/month
- **CloudTrail**: First trail is free
- **EventBridge**: Free for AWS service events
- **SES**: $0.10 per 1,000 emails
- **Secrets Manager**: $0.40/secret/month

**Total**: ~$1-5/month for typical usage

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or contributions:
1. Check existing documentation
2. Review CloudWatch Logs
3. Open an issue with details
