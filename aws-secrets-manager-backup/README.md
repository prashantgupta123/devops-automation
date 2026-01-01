# AWS Secrets Manager Backup

Automated daily backup solution for AWS Secrets Manager that stores all secrets in S3 in JSON format with date-based organization and optional email notifications.

## Features

- **Daily Automated Backups**: Scheduled backup of all AWS Secrets Manager secrets
- **S3 Storage**: Organized storage with date-based paths and latest versions
- **Email Notifications**: Optional SMTP email notifications for backup status
- **Flexible Authentication**: Multiple AWS authentication methods via AWSSession.py
- **Comprehensive Logging**: Detailed logging and error handling
- **CloudFormation Deployment**: Infrastructure as Code with proper IAM policies
- **Zero Retry Policy**: EventInvokeConfig set to 0 retries for immediate failure detection

## Architecture

```
CloudWatch Events (Daily) → Lambda Function → Secrets Manager → S3 Bucket
                                    ↓
                              Email Notification (Optional)
```

## Directory Structure

```
aws-secrets-manager-backup/
├── lambda_function.py              # Main Lambda function
├── AWSSession.py                   # AWS session management
├── Notification.py                 # Email notification module
├── input.json                      # Configuration file
├── requirements.txt                # Python dependencies
├── cloudformation-template.yml     # Infrastructure template
├── iam-policy.json                # IAM policy document
├── lambda_build.sh                # Build script
├── cloudformation_deploy.sh       # Deployment script
└── README.md                      # This file
```

## Quick Start

### 1. Configure Settings

Update `input.json` with your credentials:

```json
{
  "awsCredentials": {
    "region_name": "us-east-1",
    "profile_name": "your-profile"
  },
  "smtpCredentials": {
    "host": "smtp.gmail.com",
    "port": "587",
    "username": "your-email@gmail.com",
    "password": "your-app-password",
    "from_email": "your-email@gmail.com"
  },
  "emailNotification": {
    "email_subject": "Secrets Manager Backup Report",
    "subject_prefix": "AWS",
    "to": ["admin@company.com"]
  }
}
```

### 2. Deploy Infrastructure

```bash
# Make scripts executable
chmod +x lambda_build.sh cloudformation_deploy.sh

# Deploy the solution
./cloudformation_deploy.sh
```

### 3. Verify Deployment

Check the CloudFormation stack and Lambda function in AWS Console.

## Configuration Options

### AWS Authentication Methods

The solution supports multiple authentication methods via `AWSSession.py`:

- **Profile-based**: Uses AWS CLI profiles
- **Assumed Role**: Cross-account access via role assumption
- **Access Keys**: Direct access key authentication
- **Temporary Credentials**: STS temporary credentials
- **Default Chain**: Uses default AWS credential chain

### Email Notifications

Email notifications are optional and configured via `input.json`:

- **SMTP Configuration**: Host, port, credentials
- **Recipients**: To, CC, BCC support
- **Content**: HTML formatted backup reports

## S3 Storage Structure

Secrets are stored in S3 with the following structure:

```
s3://bucket-name/
└── secrets-manager/
    └── secret-name/
        ├── 2024/01/15/secret-name.json    # Date-based backup
        └── latest.json                     # Latest version
```

## CloudFormation Resources

The template creates:

- **S3 Bucket**: Encrypted storage with lifecycle policies
- **Lambda Function**: Python 3.13 runtime with 15-minute timeout
- **IAM Role**: Minimal required permissions
- **CloudWatch Events**: Daily schedule trigger
- **EventInvokeConfig**: Zero retry attempts
- **Log Group**: 30-day retention

All resources include comprehensive tags:
- Name, Project, Environment, Owner, CreatedBy, ManagedBy

## Security Features

- **Encryption**: S3 server-side encryption (AES256)
- **Access Control**: Minimal IAM permissions
- **Private Bucket**: Public access blocked
- **Versioning**: S3 versioning enabled
- **Lifecycle**: Automatic cleanup after 365 days

## Monitoring

- **CloudWatch Logs**: Detailed execution logs
- **Email Reports**: Success/failure notifications
- **Metrics**: Lambda execution metrics
- **Alarms**: Can be configured for failures

## Troubleshooting

### Common Issues

1. **Permission Denied**: Check IAM role permissions
2. **S3 Access**: Verify bucket exists and permissions
3. **Email Failures**: Check SMTP credentials and network access
4. **Timeout**: Increase Lambda timeout for large secret counts

### Logs

Check CloudWatch Logs at:
```
/aws/lambda/secrets-manager-backup-{environment}
```

## Customization

### Schedule Changes

Modify the `ScheduleExpression` parameter:
- `rate(1 day)` - Daily
- `rate(12 hours)` - Twice daily
- `cron(0 2 * * ? *)` - Daily at 2 AM UTC

### Retention Policy

Update S3 lifecycle rules in the CloudFormation template.

### Notification Channels

Extend `Notification.py` to support additional channels (Slack, Teams, etc.).

## Cost Optimization

- **Lambda**: Pay per execution (daily = ~$0.01/month)
- **S3**: Standard storage costs
- **CloudWatch**: Minimal logging costs
- **Lifecycle**: Automatic cleanup reduces storage costs

## Security Best Practices

1. Use IAM roles instead of access keys
2. Enable CloudTrail for audit logging
3. Regularly rotate SMTP credentials
4. Monitor access patterns
5. Use least privilege permissions

## Contributing

1. Test changes in development environment
2. Update documentation
3. Follow existing code patterns
4. Add appropriate error handling

## Support

For issues or questions:
- Check CloudWatch Logs
- Review IAM permissions
- Validate configuration files
- Test SMTP connectivity