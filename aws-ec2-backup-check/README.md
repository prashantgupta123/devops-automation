# EC2 Backup Compliance Checker

This Lambda function monitors EC2 On-Demand instances and alerts when they are not protected by AWS Backup plans. It excludes Auto Scaling Group instances and uses AWS Secrets Manager for secure SMTP credential storage.

## Features

- **Fetch On-Demand EC2 Instances**: Retrieves all running EC2 instances with On-Demand lifecycle (excludes ASG instances)
- **Check AWS Backup Protection**: Scans all backup plans to identify protected EC2 resources
- **Email Alerts**: Sends HTML email notifications for unprotected instances via AWS Secrets Manager
- **Secure Configuration**: Uses AWS Secrets Manager for SMTP credentials

## Architecture

### Core Functions

1. `get_ondemand_ec2_instances(session)` - Fetches running On-Demand EC2 instances (excludes ASG instances)
2. `get_backup_protected_resources(session)` - Gets all EC2 resources protected by AWS Backup plans
3. `check_unprotected_instances(instances, protected_resources)` - Identifies unprotected instances
4. `send_email_alert(session, smtp_secret_name, notification_config, unprotected_instances)` - Sends email alerts

### Supporting Modules

- `AWSSession.py` - Handles AWS session creation with multiple authentication methods
- `Notification.py` - Manages email notifications using AWS Secrets Manager

## Configuration

### 1. AWS Secrets Manager Setup

Create a secret in AWS Secrets Manager with SMTP credentials:

```json
{
  "SMTP_HOST": "email-smtp.region.amazonaws.com",
  "SMTP_PORT": "587",
  "SMTP_USERNAME": "your-smtp-username",
  "SMTP_PASSWORD": "your-smtp-password",
  "EMAIL_FROM": "sender@domain.com"
}
```

### 2. Update input.json

Configure AWS credentials and notification settings:

```json
{
  "awsCredentials": {
    "account_id": "your-account-id",
    "region_name": "your-region",
    "profile_name": "",
    "role_arn": "",
    "access_key": "your-access-key",
    "secret_access_key": "your-secret-key",
    "session_token": ""
  },
  "smtp_secret_name": "your-secrets-manager-secret-name",
  "notification": {
    "email": {
      "subject_prefix": "Alert",
      "to": "recipient@domain.com",
      "cc": [],
      "bcc": []
    }
  }
}
```

## Deployment

### Prerequisites

1. Create SMTP credentials secret in AWS Secrets Manager
2. Configure `input.json` with your AWS credentials and settings
3. Ensure proper IAM permissions are in place

### Steps

1. Run the deployment script:
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

2. Upload the generated ZIP file to AWS Lambda

3. Configure Lambda function:
   - Handler: `lambda_function.lambda_handler`
   - Runtime: Python 3.13+
   - Timeout: 5 minutes
   - Memory: 256 MB (minimum)

4. Attach the IAM policy from `lambda-iam-policy.json`

## IAM Permissions Required

### Lambda Execution Role

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "backup:ListBackupPlans",
        "backup:ListBackupSelections",
        "backup:GetBackupSelection",
        "secretsmanager:GetSecretValue",
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

## Scheduling

Set up CloudWatch Events or EventBridge to trigger this function on a schedule:

```bash
# Example: Daily at 9 AM UTC
ScheduleExpression: cron(0 9 * * ? *)
```

## Email Notification

When unprotected instances are found, an HTML email is sent with the following format:

**Subject:** `[Subject Prefix] | EC2 Instances Not Protected by AWS Backup | [Date]`

**Email Content:**
```html
EC2 Instances Not Protected by AWS Backup

The following EC2 On-Demand instances are currently running but are not protected by any AWS Backup plan:

┌─────────────────────────┬──────────────────┐
│ Instance ID             │ Instance Name    │
├─────────────────────────┼──────────────────┤
│ i-1234567890abcdef0     │ WebServer-01     │
│ i-0987654321fedcba0     │ DatabaseServer   │
└─────────────────────────┴──────────────────┘

Action Required: Please ensure these instances are added to an appropriate AWS Backup plan to protect against data loss.

This is an automated alert from the EC2 Backup Compliance Monitor.
```

## Output

The function returns a JSON response with:
- `total_instances`: Total On-Demand instances found
- `protected_instances`: Number of instances protected by AWS Backup
- `unprotected_instances`: Number of unprotected instances
- `unprotected_list`: Detailed list of unprotected instances with ID and Name

### Sample Response

```json
{
  "statusCode": 200,
  "body": {
    "message": "EC2 backup compliance check completed successfully",
    "total_instances": 5,
    "protected_instances": 3,
    "unprotected_instances": 2,
    "unprotected_list": [
      {
        "InstanceId": "i-1234567890abcdef0",
        "Name": "WebServer-01"
      },
      {
        "InstanceId": "i-0987654321fedcba0",
        "Name": "DatabaseServer"
      }
    ]
  }
}
```

## Local Testing

Run locally for testing:

```bash
python lambda_function.py
```

## Troubleshooting

- Ensure AWS credentials have sufficient permissions
- Verify Secrets Manager secret exists and contains correct SMTP settings
- Check CloudWatch logs for detailed error messages
- Confirm backup plans are properly configured with EC2 resource selections