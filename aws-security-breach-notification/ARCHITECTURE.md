# Architecture Documentation

## Overview

This AWS security monitoring solution provides real-time detection and alerting for security-sensitive events across your AWS infrastructure. It uses a serverless, event-driven architecture that scales automatically and requires minimal maintenance.

## Architecture Diagram

```
┌─────────────────┐
│   CloudTrail    │ ──> Logs all AWS API calls
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  EventBridge    │ ──> Filters security-relevant events
│      Rule       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Lambda Function │ ──> Processes events & detects violations
│   + Layer       │
└────────┬────────┘
         │
         ├──> Secrets Manager (SMTP credentials)
         │
         └──> SES (Email notifications)
```

## Components

### 1. CloudTrail
- Captures all AWS API calls across your account
- Provides audit trail for security analysis
- Feeds events to EventBridge

### 2. EventBridge Rule
- Filters CloudTrail events for security-relevant actions
- Configured to match specific event names (e.g., RunInstances, CreateAccessKey)
- Triggers Lambda function when matched

### 3. Lambda Function
- **Runtime**: Python 3.14
- **Memory**: 1500 MB
- **Timeout**: 900 seconds (15 minutes)
- **Deployment**: Inline code + Lambda Layer

#### Lambda Layer Structure
```
python/
├── core/                    # Core configuration & types
│   ├── base_handler.py      # Abstract base class for handlers
│   ├── constants.py         # Whitelisted ports, CIDRs
│   ├── enums.py            # Event types (EVENT, INFO)
│   ├── event_types.py      # TypedDict for EventDetail
│   ├── exceptions.py       # Custom exception classes
│   └── settings.py         # Config from env vars & Secrets Manager
│
├── handlers/               # Event-specific handlers
│   ├── alb_handler.py      # Load balancer monitoring
│   ├── cloudtrail_handler.py  # Audit trail tampering
│   ├── ec2_handler.py      # EC2 instance & resource exposure
│   ├── iam_handler.py      # IAM user & access key events
│   ├── lambda_handler.py   # Lambda function tracking
│   ├── rds_handler.py      # RDS database exposure
│   ├── s3_handler.py       # S3 bucket public access
│   ├── security_group_handler.py  # Security group rules
│   └── vpc_handler.py      # VPC & network resources
│
├── services/
│   └── notification_service.py  # Email generation & sending
│
├── utils/
│   ├── aws_helpers.py      # Shared AWS API helpers
│   └── logger.py           # Logging configuration
│
└── main.py                 # Lambda entry point & handler registry
```

### 4. Secrets Manager
- Stores SES SMTP credentials securely
- Accessed by Lambda at runtime
- Supports credential rotation

### 5. SES (Simple Email Service)
- Sends HTML-formatted email alerts
- Requires verified sender and recipient addresses
- Supports multiple recipients

## Event Flow

1. **API Call Made**: User or service makes an AWS API call
2. **CloudTrail Logs**: CloudTrail captures the event
3. **EventBridge Filters**: Rule matches security-relevant events
4. **Lambda Invoked**: Function receives event payload
5. **Handler Processes**: Appropriate handler analyzes the event
6. **Violation Detected**: Handler returns EventDetail if violation found
7. **Email Sent**: NotificationService formats and sends alert

## Handler Pattern

Each handler follows a consistent pattern:

```python
def handle_event(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """
    Process security event and return violations.
    
    Args:
        event: CloudTrail event from EventBridge
        context: Lambda context object
    
    Returns:
        List of EventDetail dictionaries (empty if no violations)
    """
    # 1. Extract relevant data from event
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    
    # 2. Check for security violations
    if is_violation(request_params):
        # 3. Return violation details
        return [EventDetail(
            title="Human-readable description",
            resource_name="resource-id",
            # ... other fields
        )]
    
    # 4. Return empty list if no violations
    return []
```

## Scalability Considerations

### Current Design (Good for Most Use Cases)
- **Single Lambda function** handles all event types
- **Handler registry** routes events to appropriate handlers
- **Lambda Layer** keeps code organized and reusable
- **Scales automatically** with AWS Lambda

### When to Consider Refactoring

If you reach **>50 event types** or **>10,000 events/day**, consider:

1. **Separate Lambda per service domain**
   - One for EC2/VPC events
   - One for IAM events
   - One for S3/RDS events

2. **Add SQS queue** between EventBridge and Lambda
   - Provides buffering for high-volume events
   - Enables batch processing
   - Improves error handling

3. **Add DynamoDB** for event tracking
   - Store violation history
   - Enable trend analysis
   - Support compliance reporting

## Security Best Practices

1. **Least Privilege IAM**: Lambda role has minimal required permissions
2. **Secrets Management**: SMTP credentials stored in Secrets Manager
3. **Encryption**: All data encrypted at rest and in transit
4. **Audit Trail**: CloudWatch Logs retain all function executions
5. **No Hardcoded Secrets**: All sensitive data from environment/Secrets Manager

## Monitoring & Troubleshooting

### CloudWatch Logs
- Log Group: `/aws/lambda/AWS-Generic-Security-{region}`
- Retention: 7 days (configurable)
- Contains all handler execution logs

### Common Issues

1. **No emails received**
   - Check SES sender/recipient verification
   - Verify Secrets Manager configuration
   - Check Lambda execution logs

2. **Handler not triggered**
   - Verify EventBridge rule is enabled
   - Check event name matches exactly
   - Review CloudTrail event structure

3. **False positives**
   - Adjust whitelisted ports in `constants.py`
   - Modify handler logic for your use case
   - Add exclusion rules

## Cost Optimization

- **Lambda**: Free tier covers 1M requests/month
- **CloudTrail**: First trail is free
- **EventBridge**: Free for AWS service events
- **SES**: $0.10 per 1,000 emails
- **Secrets Manager**: $0.40/secret/month

**Estimated monthly cost**: $1-5 for typical usage

## Future Enhancements

1. **Slack/Teams Integration**: Add webhook notifications
2. **Auto-Remediation**: Automatically fix violations
3. **Dashboard**: Real-time visualization of security events
4. **Machine Learning**: Anomaly detection for unusual patterns
5. **Multi-Account**: Centralized monitoring across AWS Organization
