# AWS Backup Failed Monitoring

Automated monitoring solution for AWS Backup jobs that identifies failed backup operations and sends detailed reports via email. This tool helps maintain backup compliance by proactively alerting on backup failures.

## Overview

This solution monitors AWS Backup jobs over a configurable time period, identifies failed backup operations, and generates Excel reports with detailed failure information. It integrates with AWS Secrets Manager for secure email configuration and supports multiple AWS authentication methods.

## Key Features

- **Failed Backup Detection**: Automatically identifies backup jobs that have failed within the last 7 days
- **Detailed Reporting**: Generates Excel reports with backup plan names, resource details, and failure information
- **Email Notifications**: Sends automated email alerts with attached Excel reports
- **Multi-Account Support**: Works with AWS profiles, assumed roles, and access keys
- **Jenkins Integration**: Includes Jenkinsfile for automated scheduling
- **Secure Configuration**: Uses AWS Secrets Manager for email credentials

## Prerequisites

- Python 3.x
- AWS CLI configured or appropriate AWS credentials
- AWS Backup service with backup plans configured
- AWS Secrets Manager secret for email configuration
- Required IAM permissions (see `iam_policy.json`)

## Installation

1. Clone the repository and navigate to the solution directory:
```bash
cd devops-automation/aws-backup-failed-monitoring
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your AWS credentials and email settings in `inputs.yml`

## Configuration

### AWS Authentication
Configure one of the following authentication methods in `inputs.yml`:

```yaml
# Option 1: AWS Profile
profile_name: "your-profile-name"

# Option 2: Assumed Role
role_arn: "arn:aws:iam::123456789012:role/BackupMonitoringRole"

# Option 3: Access Keys (not recommended for production)
access_key: "your-access-key"
secret_key: "your-secret-key"
session_token: "your-session-token"  # Optional
```

### Email Configuration
Set up email notifications:

```yaml
Email:
  enabled: true
  secret_manager: "your-smtp-secret-name"
  details:
    subject_prefix: "AWS Backup Alert"
    to:
      - "admin@cloudplatform.com"
    cc:
      - "devops@cloudplatform.com"
```

### AWS Secrets Manager
Create a secret in AWS Secrets Manager with the following structure:
```json
{
  "SMTP_HOST": "smtp.example.com",
  "SMTP_PORT": "587",
  "SMTP_USERNAME": "your-username",
  "SMTP_PASSWORD": "your-password",
  "EMAIL_FROM": "alerts@cloudplatform.com"
}
```

## Usage

### Manual Execution
```bash
python main.py
```

### Jenkins Pipeline
The included `Jenkinsfile` provides automated scheduling:
- Runs weekly on Mondays at 5:00 AM
- Includes failure notifications via SNS
- Configurable environment variables

### Shell Script Execution
```bash
bash script.sh
```

## IAM Permissions

The solution requires the following AWS permissions (see `iam_policy.json`):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "backup:ListBackupJobs",
        "backup:GetBackupPlan",
        "backup:ListTags",
        "backup:GetBackupPlanFromJSON"
      ],
      "Resource": "*"
    }
  ]
}
```

Additional permissions needed:
- `secretsmanager:GetSecretValue` for email configuration
- `sts:AssumeRole` if using role assumption

## Output

The solution generates:

1. **Excel Report**: `backup_jobs.xlsx` containing:
   - Backup Plan Name
   - Resource Name and Type
   - Resource ARN
   - Job ID
   - Start Time
   - Job State

2. **Email Notification**: HTML email with attached Excel report

3. **Console Logs**: Detailed logging of the monitoring process

## File Structure

```
aws-backup-failed-monitoring/
├── main.py                 # Main monitoring script
├── AWSSession.py          # AWS session management
├── Notification.py        # Email notification handler
├── inputs.yml             # Configuration file
├── requirements.txt       # Python dependencies
├── iam_policy.json       # Required IAM permissions
├── Jenkinsfile           # Jenkins pipeline configuration
├── script.sh             # Shell execution script
├── .gitignore            # Git ignore rules
└── README.md             # This documentation
```

## Monitoring Logic

1. **Time Range**: Monitors backup jobs from the last 7 days
2. **Job States**: Identifies jobs with 'FAILED' status
3. **Validation**: Verifies backup plan existence before reporting
4. **Reporting**: Generates detailed Excel reports for failed jobs
5. **Notification**: Sends email alerts when failures are detected

## Troubleshooting

### Common Issues

1. **Missing Dependencies**: Ensure all packages in `requirements.txt` are installed
2. **AWS Permissions**: Verify IAM permissions match `iam_policy.json`
3. **Email Configuration**: Check AWS Secrets Manager secret format
4. **Authentication**: Ensure AWS credentials are properly configured

### Logging
The solution provides detailed logging to help with troubleshooting:
- INFO level: General operation status
- ERROR level: Specific error details and exceptions

## Security Considerations

- **Credentials**: Never commit AWS credentials to version control
- **Secrets Manager**: Use AWS Secrets Manager for email credentials
- **IAM Roles**: Prefer IAM roles over access keys for authentication
- **Least Privilege**: Apply minimal required permissions

## Jenkins Integration

The included Jenkins pipeline:
- Schedules weekly execution
- Provides build history management
- Includes failure notifications
- Supports environment-specific configuration

## Contributing

When modifying this solution:
1. Test in non-production environments first
2. Update documentation for any configuration changes
3. Follow existing code structure and naming conventions
4. Ensure security best practices are maintained

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review AWS CloudTrail logs for API call details
3. Verify IAM permissions and AWS service limits
4. Contact the DevOps team for assistance

---

**Note**: This tool monitors AWS Backup jobs and requires appropriate AWS permissions. Always test in non-production environments and ensure compliance with your organization's security policies.