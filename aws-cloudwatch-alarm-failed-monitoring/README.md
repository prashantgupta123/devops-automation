# AWS CloudWatch Alarm Failed Monitoring

Automated monitoring solution that identifies CloudWatch alarms with failed actions and sends detailed email reports. Helps maintain monitoring infrastructure health by proactively alerting on alarm action failures.

## Overview

This solution monitors CloudWatch alarms for failed actions (such as SNS notification failures, Auto Scaling action failures, etc.) and generates email reports with detailed failure information. It supports multiple AWS authentication methods and can be integrated into CI/CD pipelines.

## Key Features

- **Failed Action Detection**: Identifies CloudWatch alarms with failed action history
- **Detailed Reporting**: Provides alarm name, summary message, and error details
- **Email Notifications**: Sends HTML-formatted email reports with failure information
- **Multi-Account Support**: Works with various AWS authentication methods
- **Jenkins Integration**: Includes pipeline configuration for automated scheduling
- **Flexible Configuration**: YAML-based configuration for easy customization

## Prerequisites

- Python 3.x
- AWS CLI configured or appropriate AWS credentials
- Access to AWS CloudWatch and Secrets Manager
- SMTP server configuration stored in AWS Secrets Manager

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd devops-automation/aws-cloudwatch-alarm-failed-monitoring
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure inputs:**
   ```bash
   cp inputs.yml inputs-local.yml
   # Edit inputs-local.yml with your configuration
   ```

## Configuration

### AWS Authentication Options

Configure one of the following authentication methods in `inputs.yml`:

```yaml
# Option 1: AWS Profile
profile_name: "your-profile-name"

# Option 2: IAM Role ARN
role_arn: "arn:aws:iam::123456789012:role/YourRole"

# Option 3: Access Keys with Session Token
access_key: "AKIA..."
secret_key: "your-secret-key"
session_token: "your-session-token"

# Option 4: Access Keys Only
access_key: "AKIA..."
secret_key: "your-secret-key"

# Option 5: Default AWS credentials (leave all empty)
```

### Email Configuration

```yaml
Email:
  enabled: true
  secret_manager: "your-smtp-secrets"  # AWS Secrets Manager secret name
  details:
    subject_prefix: "Production"
    to:
      - "devops@company.com"
    cc:
      - "monitoring@company.com"
```

### SMTP Secrets Format

Store SMTP configuration in AWS Secrets Manager:

```json
{
  "SMTP_HOST": "smtp.company.com",
  "SMTP_PORT": "587",
  "SMTP_USERNAME": "notifications@company.com",
  "SMTP_PASSWORD": "your-password",
  "EMAIL_FROM": "aws-monitoring@company.com"
}
```

## Usage

### Manual Execution

```bash
# Using shell script
bash script.sh

# Direct Python execution
python main.py
```

### Jenkins Pipeline

The included `Jenkinsfile` provides:
- Weekly scheduled execution (Mondays at 5 AM)
- Automatic failure notifications via SNS
- Build artifact retention

Environment variables to configure:
```groovy
DEFAULT_ENV = "production"
REGION_NAME = "us-east-1"
REPOSITORY_NUMBER = "123456789012"
SNS_TOPIC_NAME = "prod-infra-alerts"
```

## How It Works

1. **Alarm Discovery**: Retrieves all CloudWatch alarms in the specified region
2. **History Analysis**: Examines alarm action history for failed states
3. **Error Extraction**: Collects failure details including error messages
4. **Report Generation**: Creates HTML email report with failure information
5. **Notification**: Sends email to configured recipients

## Output

The solution generates an HTML email report containing:

| Field | Description |
|-------|-------------|
| Name | CloudWatch alarm name |
| SummaryMessage | Brief description of the failure |
| ErrorMessage | Detailed error information |

## Security Considerations

- **Credentials**: Never commit actual AWS credentials to version control
- **Secrets Management**: Use AWS Secrets Manager for SMTP configuration
- **IAM Permissions**: Follow least privilege principle for AWS access
- **Email Security**: Ensure SMTP credentials are properly secured

### Required IAM Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:DescribeAlarms",
        "cloudwatch:DescribeAlarmHistory",
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "*"
    }
  ]
}
```

## Troubleshooting

### Common Issues

1. **KeyError: 'secret_access_key'**
   - Fix: Update line 108 in `main.py` to use `secret_key` instead

2. **NameError: ClientError not defined**
   - Fix: Add `from botocore.exceptions import ClientError` to `Notification.py`

3. **No alarms found**
   - Verify AWS credentials and region configuration
   - Check CloudWatch permissions

4. **Email sending fails**
   - Verify SMTP configuration in Secrets Manager
   - Check network connectivity to SMTP server

### Debug Mode

Enable detailed logging by modifying the logger level:

```python
logger.setLevel(logging.DEBUG)
```

## File Structure

```
aws-cloudwatch-alarm-failed-monitoring/
├── README.md              # This documentation
├── main.py                # Main execution script
├── AWSSession.py          # AWS session management
├── Notification.py        # Email notification handler
├── inputs.yml             # Configuration file
├── requirements.txt       # Python dependencies
├── script.sh             # Execution wrapper script
├── Jenkinsfile           # CI/CD pipeline configuration
└── .gitignore            # Git ignore rules
```

## Contributing

1. Follow existing code structure and naming conventions
2. Add appropriate error handling and logging
3. Update documentation for any new features
4. Test with multiple AWS authentication methods
5. Ensure no credentials are committed to version control

## License

This project is part of the DevOps Automation Solutions repository. See the main repository for licensing information.

## Support

For issues and questions:
- Check the troubleshooting section above
- Review CloudWatch and IAM permissions
- Verify SMTP configuration in Secrets Manager
- Check Jenkins pipeline logs for CI/CD issues