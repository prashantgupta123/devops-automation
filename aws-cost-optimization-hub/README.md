# AWS Cost Optimization Hub: Automated Recommendation Reporting

## Introduction & Problem Statement

In today's cloud-first world, managing AWS costs effectively is crucial for any organization. While AWS provides powerful cost optimization tools, manually reviewing recommendations across multiple accounts and services can be time-consuming and error-prone. Teams often struggle with:

- **Scattered Recommendations**: Cost optimization insights spread across multiple AWS accounts and regions
- **Manual Review Overhead**: Time-consuming process of checking AWS Cost Optimization Hub console regularly
- **Lack of Visibility**: No centralized view of potential savings across the organization
- **Implementation Uncertainty**: Difficulty prioritizing recommendations based on effort and impact
- **Reporting Challenges**: No automated way to share findings with stakeholders

AWS Cost Optimization Hub aggregates recommendations from services like AWS Compute Optimizer, AWS Cost Explorer, and AWS Trusted Advisor. However, accessing this data programmatically and generating actionable reports requires custom automation.

This solution addresses these challenges by providing an automated system that:
- Retrieves cost optimization recommendations from single or multiple AWS accounts
- Generates comprehensive Excel reports with detailed analysis
- Sends email notifications with executive summaries
- Groups recommendations by resource type for easier prioritization
- Provides implementation guidance with effort estimates and rollback information

## Architecture / Design Overview

The solution follows a modular, serverless-ready architecture that can run as a standalone script or be deployed as an AWS Lambda function.

![AWS Cost Optimization Architecture](generated-diagrams/aws_cost_optimization_architecture.png)

### Architecture Components

**1. Authentication Layer (AWSSession.py)**
- Supports multiple AWS authentication methods (profiles, roles, access keys, STS tokens)
- Handles cross-account access via IAM role assumption
- Provides session management with proper error handling

**2. Data Retrieval Layer (function.py)**
- Connects to AWS Cost Optimization Hub API
- Implements pagination for large datasets
- Aggregates data from multiple accounts
- Processes recommendations and summaries

**3. Report Generation Layer (function.py)**
- Creates multi-sheet Excel workbooks with xlsxwriter
- Implements custom formatting and styling
- Groups recommendations by resource type
- Calculates total savings and recommendation counts

**4. Notification Layer (Notification.py)**
- Sends HTML-formatted email notifications
- Attaches Excel reports
- Supports multiple recipients (To, CC, BCC)
- Handles SMTP authentication securely

### Data Flow

```
┌─────────────────┐
│  Configuration  │
│  (input.json)   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│     AWS Session Management              │
│  (Profile/Role/Keys/STS Authentication) │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│   AWS Cost Optimization Hub API         │
│  • list_recommendation_summaries()      │
│  • list_recommendations()               │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│      Data Processing & Aggregation      │
│  • Multi-account data merging           │
│  • Resource type grouping               │
│  • Savings calculation                  │
└────────┬────────────────────────────────┘
         │
         ├──────────────────┬──────────────┐
         ▼                  ▼              ▼
┌────────────────┐  ┌──────────────┐  ┌──────────────┐
│ Excel Report   │  │ HTML Email   │  │ JSON Logs    │
│ Generation     │  │ Notification │  │ (Optional)   │
└────────────────┘  └──────────────┘  └──────────────┘
```

### Key Design Decisions

**Modular Architecture**: Separation of concerns with dedicated modules for authentication, notification, and data processing enables easy testing and maintenance.

**Flexible Authentication**: Supporting multiple authentication methods allows the solution to work in various environments (local development, CI/CD pipelines, Lambda functions).

**Multi-Account Support**: Two operational modes (single account via input.json or multiple accounts via account_details.json) provide flexibility for different organizational structures.

**Comprehensive Reporting**: Excel format with multiple sheets (summary, all recommendations, and resource-type-specific sheets) enables different stakeholders to focus on relevant data.

**Pagination Handling**: Automatic pagination ensures all recommendations are retrieved regardless of dataset size.

## Solution Approach

### Core Functionality

The solution implements a three-phase approach:

**Phase 1: Data Collection**
- Authenticate with AWS using configured credentials
- Query Cost Optimization Hub for recommendation summaries (aggregated by resource type)
- Retrieve detailed recommendations with full metadata
- Handle pagination automatically to ensure complete data retrieval

**Phase 2: Data Processing**
- Aggregate data from multiple accounts (if configured)
- Enrich recommendations with account names and identifiers
- Group recommendations by resource type for analysis
- Calculate total savings and recommendation counts

**Phase 3: Reporting & Notification**
- Generate multi-sheet Excel workbook with formatted data
- Create HTML email with executive summary
- Send notifications with attached reports
- Log all operations for audit trail

### Multi-Account Strategy

The solution intelligently detects the operational mode:

**Single Account Mode**: When only `input.json` exists, processes a single AWS account with credentials from the configuration file.

**Multi-Account Mode**: When `account_details.json` exists, iterates through all configured accounts, aggregates data, and generates a consolidated report.

This approach provides flexibility without requiring code changes—simply add or remove the `account_details.json` file to switch modes.

## Code Walkthrough

### Authentication Module (AWSSession.py)

The authentication module provides a unified interface for AWS session creation:

```python
def get_aws_session(credentials: Dict[str, Any]) -> boto3.Session:
    """Create AWS session with flexible authentication methods."""
    region = credentials.get("region_name", "us-east-1")
    
    # Priority order: Profile > Role > Temp Credentials > Access Keys > Default
    if credentials.get("profile_name"):
        return boto3.Session(profile_name=credentials["profile_name"], region_name=region)
    elif credentials.get("role_arn"):
        return _create_assumed_role_session(credentials["role_arn"], region)
    # ... additional methods
```

**Key Features**:
- Cascading authentication with priority order
- Automatic role assumption for cross-account access
- Comprehensive error handling and logging
- Type hints for better IDE support

### Data Retrieval Logic (function.py)

The core retrieval functions implement pagination and error handling:

```python
def list_recommendations(client, max_results: int = 50) -> dict:
    """Retrieve detailed recommendations with automatic pagination."""
    all_items = []
    next_token = None
    
    while True:
        params = {
            'maxResults': max_results,
            'includeAllRecommendations': True,
            'orderBy': {'dimension': 'ResourceType', 'order': 'Asc'}
        }
        if next_token:
            params['nextToken'] = next_token
        
        response = client.list_recommendations(**params)
        all_items.extend(response.get('items', []))
        
        next_token = response.get('nextToken')
        if not next_token:
            break
    
    response['items'] = all_items
    return response
```

**Implementation Highlights**:
- Automatic pagination handling ensures complete data retrieval
- Ordering by resource type enables logical grouping
- `includeAllRecommendations` flag captures all available insights
- Defensive programming with `.get()` prevents KeyError exceptions

### Excel Report Generation

The report generation creates a professional, multi-sheet workbook:

```python
def create_excel_report(summaries: dict, recommendations: dict, config: dict) -> str:
    """Create Excel report with summaries and recommendations."""
    workbook = xlsxwriter.Workbook(filename)
    
    # Define reusable formats
    header_format = workbook.add_format({
        "bold": True, "align": "center", "fg_color": "#D7E4BC", "border": 1
    })
    
    currency_format = workbook.add_format({
        "border": 1, "num_format": '"$"#,##0.00'
    })
    
    # Create summary sheet
    summary_sheet = workbook.add_worksheet("Summary")
    # ... populate with aggregated data
    
    # Create detailed recommendations sheet
    rec_sheet = workbook.add_worksheet("All Recommendations")
    # ... populate with full details
    
    # Create resource-type-specific sheets
    grouped = defaultdict(list)
    for item in items:
        grouped[item.get('currentResourceType', 'Unknown')].append(item)
    
    for resource_type, type_items in grouped.items():
        type_sheet = workbook.add_worksheet(resource_type[:31])
        # ... populate with filtered data
```

**Report Structure**:
- **Summary Sheet**: High-level overview with total savings by resource type
- **All Recommendations Sheet**: Complete dataset with all fields
- **Resource-Type Sheets**: Filtered views for EC2, RDS, Lambda, etc.

### Email Notification System

The notification module handles email delivery with attachments:

```python
def send_email(smtp_config: Dict[str, str], email_details: Dict[str, Any], 
               content: str) -> None:
    """Send email notification with comprehensive error handling."""
    message = _build_email_message(smtp_config, email_details, content)
    recipients = _get_all_recipients(email_details)
    _send_via_smtp(smtp_config, message, recipients)
```

**Email Features**:
- HTML formatting with CSS styling for professional appearance
- Automatic date stamping in subject line
- Support for multiple recipients across To, CC, and BCC fields
- File attachment handling for Excel reports
- Comprehensive error handling with detailed logging

## Configuration & Setup Instructions

### Prerequisites

- Python 3.13+ (compatible with 3.8+)
- AWS account with Cost Optimization Hub enabled
- IAM permissions for Cost Optimization Hub API access
- SMTP server access for email notifications (optional)

### Required IAM Permissions

Create an IAM policy with the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cost-optimization-hub:ListRecommendations",
        "cost-optimization-hub:ListRecommendationSummaries",
        "cost-optimization-hub:GetRecommendation"
      ],
      "Resource": "*"
    }
  ]
}
```

For cross-account access, configure a trust relationship in the target account's IAM role.

### Installation Steps

**1. Clone the repository**
```bash
git clone <repository-url>
cd devops-automation/aws-cost-optimization-hub
```

**2. Install dependencies**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**3. Configure AWS credentials**

**Option A: Single Account (input.json)**
```json
{
  "awsCredentials": {
    "account_id": "123456789012",
    "account_name": "Production",
    "region_name": "us-east-1",
    "profile_name": "default"
  },
  "smtpCredentials": {
    "host": "smtp.gmail.com",
    "port": "587",
    "username": "your-email@example.com",
    "password": "your-app-password",
    "from_email": "your-email@example.com"
  },
  "emailNotification": {
    "email_subject": "AWS Cost Optimization Hub Report",
    "subject_prefix": "Production",
    "to": ["team@example.com"],
    "cc": ["manager@example.com"]
  }
}
```

**Option B: Multiple Accounts (account_details.json)**
```json
[
  {
    "cloudName": "AWS",
    "regionName": "us-east-1",
    "projectName": "Production",
    "accountId": "123456789012",
    "accountName": "Prod-Account",
    "roleName": "AdministratorAccess",
    "accountKeys": {
      "profile_name": "prod-profile"
    }
  },
  {
    "cloudName": "AWS",
    "regionName": "us-east-1",
    "projectName": "Development",
    "accountId": "987654321098",
    "accountName": "Dev-Account",
    "accountKeys": {
      "role_arn": "arn:aws:iam::987654321098:role/CostOptimizationRole"
    }
  }
]
```

### Authentication Methods

The solution supports multiple authentication approaches:

**1. AWS Profile** (Recommended for local development)
```json
"accountKeys": {
  "profile_name": "my-profile"
}
```

**2. IAM Role Assumption** (Recommended for cross-account access)
```json
"accountKeys": {
  "role_arn": "arn:aws:iam::123456789012:role/CostOptRole"
}
```

**3. Access Keys** (Use with caution, prefer IAM roles)
```json
"accountKeys": {
  "access_key": "AKIAIOSFODNN7EXAMPLE",
  "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
}
```

**4. Temporary Credentials** (For STS-based authentication)
```json
"accountKeys": {
  "access_key": "ASIAIOSFODNN7EXAMPLE",
  "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
  "key_session_token": "FwoGZXIvYXdzEBYaD..."
}
```

## Usage Examples

### Basic Execution

**Single Account Mode**:
```bash
# Ensure only input.json exists
python function.py
```

**Multi-Account Mode**:
```bash
# Ensure both input.json and account_details.json exist
python function.py
```

### Using the Shell Script

The included shell script automates the entire process:

```bash
chmod +x script.sh
./script.sh
```

This script:
- Creates a Python virtual environment
- Installs dependencies
- Executes the main function
- Cleans up the virtual environment
- Provides detailed execution logs

### Jenkins Pipeline Integration

Create a Jenkins pipeline job with the following configuration:

```groovy
pipeline {
    agent any
    
    stages {
        stage('Setup') {
            steps {
                sh 'python3 -m venv venv'
                sh '. venv/bin/activate && pip install -r requirements.txt'
            }
        }
        
        stage('Generate Report') {
            steps {
                sh '. venv/bin/activate && python function.py'
            }
        }
        
        stage('Archive Report') {
            steps {
                archiveArtifacts artifacts: '*.xlsx', fingerprint: true
            }
        }
    }
    
    post {
        always {
            sh 'rm -rf venv'
        }
    }
}
```

### Scheduled Execution with Cron

For automated weekly reports:

```bash
# Edit crontab
crontab -e

# Add entry for Monday 9 AM execution
0 9 * * 1 cd /path/to/aws-cost-optimization-hub && ./script.sh >> /var/log/cost-optimization.log 2>&1
```

### Output Files

After execution, you'll find:

- `aws_cost_optimization_report.xlsx` - Comprehensive Excel report
- Console logs with execution details
- Email notification sent to configured recipients

## Best Practices Followed

### 1. Security First

**No Hardcoded Credentials**: All sensitive information is externalized to configuration files that should be excluded from version control.

**Least Privilege Access**: IAM permissions are scoped to only Cost Optimization Hub read operations.

**Secure Communication**: SMTP connections use STARTTLS encryption for email transmission.

**Credential Hierarchy**: Authentication methods follow a priority order, preferring more secure options (profiles, roles) over static credentials.

### 2. Code Quality

**Type Hints**: All functions include type annotations for better IDE support and early error detection.

**Comprehensive Logging**: Structured logging at INFO and ERROR levels provides visibility into execution flow.

**Error Handling**: Try-except blocks with specific exception handling prevent silent failures.

**Modular Design**: Separation of concerns enables independent testing and maintenance of components.

### 3. Operational Excellence

**Idempotent Operations**: Script can be run multiple times without side effects.

**Pagination Handling**: Automatic handling of large datasets ensures complete data retrieval.

**Graceful Degradation**: Email notification failures don't prevent report generation.

**Audit Trail**: Comprehensive logging provides accountability and troubleshooting capability.

### 4. Cost Optimization

**Efficient API Usage**: Batched requests with pagination minimize API calls.

**Resource Cleanup**: Virtual environment cleanup in shell script prevents disk space accumulation.

**Serverless-Ready**: Architecture supports Lambda deployment for event-driven execution.

## Security & Performance Considerations

### Security Considerations

**1. Credential Management**

Never commit `input.json` or `account_details.json` with real credentials. Use `.gitignore`:

```gitignore
input.json
account_details.json
*.xlsx
*.log
venv/
__pycache__/
```

**2. SMTP Security**

For Gmail SMTP, use App Passwords instead of account passwords:
- Enable 2-factor authentication
- Generate an App Password at https://myaccount.google.com/apppasswords
- Use the generated password in `smtpCredentials`

**3. Cross-Account Access**

When using role assumption, implement proper trust relationships:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::SOURCE_ACCOUNT:root"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "unique-external-id"
        }
      }
    }
  ]
}
```

**4. Data Sensitivity**

Cost optimization reports may contain sensitive business information. Ensure:
- Email recipients are authorized to view cost data
- Reports are stored in secure locations
- Access logs are maintained for compliance

### Performance Considerations

**1. API Rate Limits**

AWS Cost Optimization Hub has API rate limits. For large-scale deployments:
- Implement exponential backoff for retries
- Consider caching recommendations for short periods
- Stagger execution across multiple accounts

**2. Memory Usage**

For accounts with thousands of recommendations:
- Current implementation loads all data into memory
- Consider streaming processing for very large datasets
- Monitor Lambda memory usage if deploying serverless

**3. Execution Time**

Typical execution times:
- Single account: 10-30 seconds
- 10 accounts: 2-5 minutes
- 50+ accounts: Consider parallel processing

**4. Excel File Size**

Large reports (10,000+ recommendations) may result in files exceeding email attachment limits:
- Consider uploading to S3 and sending download links
- Implement report splitting by account or resource type
- Use compression for email attachments

## Common Pitfalls & Troubleshooting

### Issue 1: "Cost Optimization Hub is not enabled"

**Symptom**: Error message indicating Cost Optimization Hub is not available.

**Solution**: Enable Cost Optimization Hub in the AWS Console:
1. Navigate to AWS Cost Management Console
2. Select "Cost Optimization Hub" from the left menu
3. Click "Get Started" and follow the enrollment process
4. Wait 24-48 hours for initial data population

### Issue 2: "Access Denied" errors

**Symptom**: Boto3 raises `ClientError` with "AccessDenied" message.

**Root Causes**:
- Missing IAM permissions
- Incorrect role assumption configuration
- Expired temporary credentials

**Solution**:
```bash
# Verify credentials
aws sts get-caller-identity --profile your-profile

# Test Cost Optimization Hub access
aws cost-optimization-hub list-recommendation-summaries --region us-east-1
```

### Issue 3: Empty recommendations

**Symptom**: Report generated but contains no recommendations.

**Possible Causes**:
- Cost Optimization Hub recently enabled (data not yet available)
- All resources already optimized
- Insufficient usage data for recommendations

**Solution**: Wait 24-48 hours after enabling Cost Optimization Hub for initial recommendations to appear.

### Issue 4: SMTP authentication failures

**Symptom**: Email sending fails with authentication errors.

**Common Issues**:
- Gmail blocking "less secure apps"
- Incorrect SMTP port (use 587 for STARTTLS)
- Firewall blocking outbound SMTP connections

**Solution for Gmail**:
```json
{
  "smtpCredentials": {
    "host": "smtp.gmail.com",
    "port": "587",
    "username": "your-email@gmail.com",
    "password": "your-16-char-app-password",
    "from_email": "your-email@gmail.com"
  }
}
```

### Issue 5: Excel file corruption

**Symptom**: Generated Excel file cannot be opened.

**Cause**: Script interrupted during file writing.

**Solution**: Ensure script completes successfully. Check logs for errors during report generation.

### Issue 6: Multi-account mode not working

**Symptom**: Only single account processed despite `account_details.json` existing.

**Solution**: Verify `account_details.json` is valid JSON and in the same directory as `function.py`:

```bash
# Validate JSON syntax
python -m json.tool account_details.json

# Check file location
ls -la account_details.json
```

## Enhancements & Future Improvements

### Planned Enhancements

**1. AWS Lambda Deployment**

Package the solution as a Lambda function with:
- CloudFormation/Terraform infrastructure as code
- EventBridge scheduled execution
- S3 storage for generated reports
- SNS integration for notifications

**2. Advanced Filtering**

Implement recommendation filtering by:
- Minimum savings threshold
- Implementation effort level
- Resource tags
- Specific AWS services
- Rollback capability

**3. Historical Tracking**

Store recommendation history to:
- Track implementation progress
- Measure actual vs. estimated savings
- Identify recurring optimization opportunities
- Generate trend analysis reports

**4. Integration Enhancements**

- **Slack/Teams Integration**: Send notifications to collaboration platforms
- **Jira Integration**: Automatically create tickets for high-value recommendations
- **ServiceNow Integration**: Create change requests for implementation
- **Grafana Dashboard**: Visualize cost optimization metrics

**5. Advanced Reporting**

- **PDF Reports**: Generate executive-friendly PDF summaries
- **Interactive Dashboards**: Web-based visualization of recommendations
- **Comparative Analysis**: Compare optimization progress across time periods
- **ROI Tracking**: Measure actual savings from implemented recommendations

### Contribution Ideas

**Easy (Good First Issues)**:
- Add support for additional SMTP providers
- Implement CSV export format
- Add command-line arguments for configuration file paths
- Create Docker container for easy deployment

**Medium**:
- Implement recommendation filtering logic
- Add support for AWS Organizations integration
- Create CloudFormation template for Lambda deployment
- Implement parallel processing for multi-account scenarios

**Advanced**:
- Build web UI for report visualization
- Implement machine learning for recommendation prioritization
- Create automated implementation workflows
- Develop cost optimization recommendation engine

## Conclusion

AWS Cost Optimization Hub provides valuable insights, but manual review doesn't scale. This automated solution transforms raw API data into actionable intelligence, enabling organizations to:

- **Save Time**: Automated report generation eliminates manual console navigation
- **Increase Visibility**: Centralized reporting across multiple accounts and services
- **Accelerate Implementation**: Detailed recommendations with effort estimates and rollback information
- **Improve Accountability**: Regular email reports keep stakeholders informed
- **Optimize Continuously**: Scheduled execution ensures ongoing cost optimization

### Key Takeaways

1. **Modular Architecture**: Separation of concerns enables easy maintenance and testing
2. **Flexible Authentication**: Multiple authentication methods support various deployment scenarios
3. **Comprehensive Reporting**: Multi-sheet Excel reports cater to different stakeholder needs
4. **Production-Ready**: Error handling, logging, and security best practices built-in
5. **Extensible Design**: Easy to add new features like filtering, historical tracking, or integrations

### Getting Started

The fastest way to start optimizing your AWS costs:

```bash
# Clone and setup
git clone <repository-url>
cd devops-automation/aws-cost-optimization-hub
pip install -r requirements.txt

# Configure (use example files as templates)
cp input.json.example input.json
# Edit input.json with your credentials

# Run
python function.py
```

Within minutes, you'll have a comprehensive cost optimization report in your inbox, ready for review and implementation.

### Resources

- [AWS Cost Optimization Hub Documentation](https://docs.aws.amazon.com/cost-management/latest/userguide/cost-optimization-hub.html)
- [AWS Cost Management Best Practices](https://aws.amazon.com/aws-cost-management/cost-optimization/)
- [Boto3 Cost Optimization Hub API Reference](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cost-optimization-hub.html)

---

## Contact & Support

**Author**: Prashant Gupta  
**GitHub**: https://github.com/prashantgupta123/  
**LinkedIn**: https://www.linkedin.com/in/prashantgupta123/

**Questions or feedback?** Open an issue or submit a pull request!

---

*This solution is part of the [DevOps Automation Solutions](https://github.com/prashantgupta123/devops-automation) repository—a comprehensive collection of production-ready automation tools for cloud infrastructure management.*

**⭐ If you found this helpful, please star the repository!**

---