# AWS Cost Explorer Report

Automated AWS cost analysis and reporting tool that generates detailed cost breakdowns by region, service, and account with Excel export functionality.

## Features

- **Multi-Account Support**: Process multiple AWS accounts simultaneously
- **Cost Breakdown**: Analyze costs by region, service, and region-service combinations
- **Excel Export**: Generate comprehensive Excel reports with multiple sheets
- **Security Scanning**: Integration with Prowler and Scout Suite for security assessments
- **Flexible Authentication**: Support for profiles, roles, and temporary credentials

## Prerequisites

- Python 3.7+
- AWS CLI configured
- Appropriate AWS permissions for Cost Explorer API
- Required Python packages (see requirements.txt)

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd devops-automation/aws-cost-explorer-report

# Install dependencies
pip install -r requirements.txt
```

## Configuration

### Account Details Setup

Create `account_details.json` with your AWS account information:

```json
[
    {
        "cloudName": "AWS",
        "regionName": "us-east-1",
        "projectName": "MyProject",
        "accountId": "999999999999",
        "accountName": "myproject-nonprod",
        "roleName": "myproject_ro",
        "accountKeys": {
            "profile_name": "",
            "role_arn": "arn:aws:iam::999999999999:role/myproject_ro",
            "access_key": "",
            "secret_access_key": "",
            "key_session_token": ""
        }
    }
]
```

### Authentication Methods

The tool supports multiple authentication methods:

1. **AWS Profile**: Set `profile_name` in accountKeys
2. **IAM Role**: Set `role_arn` in accountKeys
3. **Temporary Credentials**: Set `access_key`, `secret_access_key`, and `key_session_token`
4. **Default Credentials**: Leave all fields empty to use default AWS credentials

## Usage

### Generate Cost Report

```bash
# Generate cost breakdown JSON
python function.py

# Convert to Excel report
python excel_export.py
```

### Security Scanning (Optional)

```bash
# Run Prowler security scan
chmod +x prowler-script.sh
./prowler-script.sh

# Run Scout Suite security scan
chmod +x scout-script.sh
./scout-script.sh
```

## Output Files

### JSON Output
- `cost_breakdown_by_region.json`: Detailed cost data for all accounts

### Excel Report
- `aws_cost_report.xlsx`: Multi-sheet Excel report containing:
  - **Summary**: Account totals and overview
  - **Regions**: Cost breakdown by region across accounts
  - **Services**: Cost breakdown by service across accounts
  - **Individual Account Sheets**: Detailed breakdown per account

## File Structure

```
aws-cost-explorer-report/
├── function.py                           # Main cost analysis script
├── excel_export.py                       # Excel report generator
├── AWSSession.py                         # AWS session management
├── account_details.json                  # Account configuration
├── requirements.txt                      # Python dependencies
├── prowler-script.sh                     # Prowler security scan
├── scout-script.sh                       # Scout Suite security scan
├── example_cost_breakdown_by_region.json # Sample output format
└── README.md                            # This file
```

## API Permissions Required

Ensure your AWS credentials have the following permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ce:GetCostAndUsage",
                "ce:GetUsageReport",
                "ce:DescribeCostCategoryDefinition"
            ],
            "Resource": "*"
        }
    ]
}
```

## Cost Analysis Details

### Time Period
- Analyzes the previous month's costs (from first day of previous month to first day of current month)

### Grouping Dimensions
- **Region**: AWS regions where resources are deployed
- **Service**: AWS services being used
- **Region-Service**: Combined breakdown for detailed analysis

### Cost Metrics
- Uses `UnblendedCost` metric for accurate cost representation
- Rounds costs to 2 decimal places
- Excludes zero-cost items from reports

## Troubleshooting

### Common Issues

1. **Permission Denied**: Ensure AWS credentials have Cost Explorer permissions
2. **No Data**: Check if the account has any costs in the previous month
3. **Authentication Errors**: Verify account credentials and role assumptions

### Debug Mode

Add debug logging to function.py:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Security Best Practices

- Never commit actual credentials to version control
- Use IAM roles with least privilege access
- Regularly rotate access keys
- Enable CloudTrail for API call auditing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Create GitHub issues for bug reports
- Include account configuration (without credentials)
- Provide error messages and logs