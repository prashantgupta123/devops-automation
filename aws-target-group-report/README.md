# Target Group Error Rate Monitor

This Lambda function monitors AWS Application Load Balancer target groups for high error rates and sends email reports.

## Features

- Fetches CloudWatch metrics for target groups over the last 7 days
- Calculates error percentage: (3XX + 4XX) / 2XX * 100
- Identifies target groups with error rate > 5%
- Sends detailed HTML email reports
- Supports testing with a single target group before processing all

## Configuration

Update `input.json` with your AWS credentials and email settings:

```json
{
  "awsCredentials": {
    "account_id": "your-account-id",
    "region_name": "ap-south-1",
    "access_key": "your-access-key",
    "secret_access_key": "your-secret-key"
  },
  "smtpCredentials": {
    "host": "email-smtp.ap-south-1.amazonaws.com",
    "port": "587",
    "username": "your-smtp-username",
    "password": "your-smtp-password",
    "from_email": "your-from-email"
  },
  "notification": {
    "email": {
      "subject_prefix": "YourCompany",
      "to": "recipient@example.com",
      "cc": [],
      "bcc": []
    }
  }
}
```

## Usage

### Local Testing

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Test with single target group:
```bash
python test_local.py
```

3. Or run directly:
```bash
python lambda_function.py
```

### Lambda Deployment

1. Package the function:
```bash
./deploy.sh
```

2. Deploy to AWS Lambda with the following event structure:

**Test single target group:**
```json
{
  "fetch_all": false
}
```

**Process all target groups:**
```json
{
  "fetch_all": true
}
```

## Metrics Collected

- **HTTPCode_Target_2XX_Count**: Successful responses
- **HTTPCode_Target_3XX_Count**: Redirection responses  
- **HTTPCode_Target_4XX_Count**: Client error responses

## Error Calculation

Error Percentage = ((3XX Count + 4XX Count) / 2XX Count) × 100

Target groups with error percentage > 5% are flagged in the report.

## Email Report

The email report includes:
- Test target group results
- Table of target groups exceeding 5% error rate
- Detailed metrics breakdown (2XX, 3XX, 4XX counts)
- 7-day analysis period

## IAM Permissions Required

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "elasticloadbalancing:DescribeTargetGroups",
        "cloudwatch:GetMetricStatistics"
      ],
      "Resource": "*"
    }
  ]
}
```
