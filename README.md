# DevOps Automation Solutions

A comprehensive collection of DevOps automation tools and scripts for cloud infrastructure management, CI/CD pipelines, and operational tasks.

## Repository Structure

```
devops-automation/
├── aws-agentcore-runtime/             # AWS Bedrock AgentCore AI agent deployment
├── aws-backup-failed-monitoring/       # AWS Backup job failure monitoring
├── aws-cloudwatch-alarm-failed-monitoring/ # CloudWatch alarm action failure monitoring
├── aws-cost-explorer-report/           # AWS cost analysis and reporting
├── aws-cw-orphan-alarms/              # CloudWatch orphaned alarms cleanup
├── aws-ec2-backup-check/              # EC2 backup validation automation
├── aws-ec2-spot-interruption-notification/ # EC2 Spot Instance interruption alerts
├── aws-ecs-service-monitoring/        # ECS service monitoring and alerting
├── aws-guardduty-notification/        # GuardDuty multi-channel alert system
├── aws-iam-identity-accounts-sso/     # AWS SSO credential automation
├── aws-news/                          # AWS news aggregation service
├── aws-target-group-report/           # Target group health reporting
├── kong-service-routes/               # Kong API Gateway automation
├── npm-vulnerability-report/          # NPM security vulnerability scanning
├── unauthenticated-apis-report/       # API authentication security scanning
└── README.md                          # This file
```

## Solutions Overview

### 🤖 AWS Bedrock AgentCore Runtime
**Location:** `aws-agentcore-runtime/`

Comprehensive solution for building, deploying, and managing AI agents using AWS Bedrock AgentCore Runtime. Provides a serverless, fully managed environment for running AI agents at scale with enterprise-grade security and performance.

**Key Features:**
- Serverless AI agent deployment using AWS Bedrock AgentCore
- Integration with Claude 3 Haiku model for natural language processing
- Automated build and deployment pipeline with S3 storage
- Production-ready Python implementation with error handling and logging
- Direct API invocation and Lambda integration support
- Comprehensive monitoring and observability features
- Security best practices and compliance considerations

### 💾 AWS Backup Failed Monitoring
**Location:** `aws-backup-failed-monitoring/`

Automated monitoring solution for AWS Backup jobs that identifies failed backup operations and sends detailed reports via email. Helps maintain backup compliance by proactively alerting on backup failures.

**Key Features:**
- Failed backup job detection over configurable time periods
- Excel report generation with detailed failure information
- Email notifications with attached reports
- Multi-account support with various authentication methods
- Jenkins pipeline integration for automated scheduling

### 🔐 AWS Secrets Manager Backup
**Location:** `aws-secrets-manager-backup/`

Automated daily backup solution for AWS Secrets Manager that stores all secrets in S3 in JSON format. Provides comprehensive backup management with date-based organization and optional email notifications.

**Key Features:**
- Daily automated backup of all AWS Secrets Manager secrets
- S3 storage with date-based organization and latest versions
- Optional SMTP email notifications for backup status reports
- Flexible AWS authentication methods (profile, role, keys, STS)
- CloudFormation deployment with EventInvokeConfig (0 retries)
- Comprehensive logging and error handling
- S3 lifecycle policies for automatic cleanup
- Production-ready security with encryption and access controls

### 💰 AWS Cost Explorer Report
**Location:** `aws-cost-explorer-report/`

Generates comprehensive AWS cost analysis reports with breakdowns by service, region, and account. Includes integration with Prowler and AWS Scout Suite for security assessments.

**Key Features:**
- Cost breakdown by service and region
- Excel export functionality
- Multi-account cost aggregation
- Security scanning integration

### 🔔 AWS CloudWatch Orphan Alarms
**Location:** `aws-cw-orphan-alarms/`

Identifies and manages orphaned CloudWatch alarms that reference deleted resources. Helps maintain clean monitoring infrastructure and reduce costs.

**Key Features:**
- Automated orphan alarm detection
- Jenkins pipeline integration
- Email notifications
- Multi-account support

### ⚠️ AWS CloudWatch Alarm Failed Monitoring
**Location:** `aws-cloudwatch-alarm-failed-monitoring/`

Monitors CloudWatch alarms for failed actions and sends detailed email reports. Helps maintain monitoring infrastructure health by proactively alerting on alarm action failures.

**Key Features:**
- Failed alarm action detection
- Detailed error reporting with HTML email format
- Multi-account authentication support
- Jenkins pipeline integration for automated scheduling
- SMTP configuration via AWS Secrets Manager

### 💾 AWS EC2 Backup Check
**Location:** `aws-ec2-backup-check/`

Validates EC2 instance backup compliance and sends notifications for instances without proper backup configurations. Deployable as Lambda function.

**Key Features:**
- Automated backup validation
- CloudFormation deployment
- Email notifications via SES
- Scheduled execution support

### 🚨 AWS EC2 Spot Interruption Notification
**Location:** `aws-ec2-spot-interruption-notification/`

Automated notification system for AWS EC2 Spot Instance interruption warnings. Monitors spot instance interruption events and sends alerts via multiple channels including SNS, Google Chat, and SMTP email.

**Key Features:**
- Multi-channel notifications (SNS, Google Chat, SMTP email)
- ECS service detection on interrupted instances
- Flexible AWS authentication methods
- CloudFormation deployment with automated scripts
- Real-time spot interruption monitoring
- Service impact assessment and reporting

### 🔐 AWS IAM Identity & SSO Management
**Location:** `aws-iam-identity-accounts-sso/`

Automates AWS SSO authentication and credential extraction for multiple accounts and roles. Streamlines access management across different AWS environments.

**Key Features:**
- Automated SSO device flow authentication
- Multi-account credential extraction
- JSON output for integration with other tools
- Support for multiple roles per account

### 📰 AWS News Aggregator
**Location:** `aws-news/`

Serverless Lambda function that aggregates and delivers AWS news and updates. Includes Terraform infrastructure as code for deployment.

**Key Features:**
- Automated AWS news collection
- Terraform deployment
- Serverless architecture
- Scheduled news delivery

### 🎯 AWS Target Group Report
**Location:** `aws-target-group-report/`

Generates health and status reports for AWS Application Load Balancer target groups. Monitors target health and sends notifications.

**Key Features:**
- Target health monitoring
- Automated reporting
- Lambda-based execution
- Email notifications

### 🔍 AWS ECS Service Monitoring
**Location:** `aws-ecs-service-monitoring/`

Automated monitoring solution for AWS ECS services that detects service failures, deployment issues, and task placement problems. Sends real-time notifications via SNS and creates custom CloudWatch metrics.

**Key Features:**
- Real-time ECS service event monitoring
- Automated failure detection and alerting
- Custom CloudWatch metrics creation
- SNS notification integration
- Terraform infrastructure as code
- Support for multiple clusters and services

### 🛡️ AWS GuardDuty Multi-Channel Notification
**Location:** `aws-guardduty-notification/`

Comprehensive serverless solution for processing AWS GuardDuty security findings and delivering intelligent notifications across multiple channels. Built with enterprise-grade security and reliability in mind.

**Key Features:**
- Real-time GuardDuty finding processing via EventBridge
- Multi-channel notifications (SNS, Email, Google Chat)
- Flexible AWS authentication methods
- Production-ready error handling and logging
- CloudFormation infrastructure as code
- Automated deployment scripts
- Severity-based alert formatting
- Comprehensive security best practices

### 🌐 Kong Service Routes Automation
**Location:** `kong-service-routes/`

Automated Kong API Gateway service and route management tool that creates and configures Kong services, routes, plugins, and consumers based on JSON configuration.

**Key Features:**
- Automated service and route creation
- Plugin configuration management
- Consumer and credential management
- Duplicate prevention validation
- Comprehensive logging system

### 🔒 NPM Vulnerability Report
**Location:** `npm-vulnerability-report/`

Scans GitHub and GitLab repositories for NPM package vulnerabilities. Generates consolidated security reports across multiple repositories.

**Key Features:**
- GitHub and GitLab integration
- NPM audit automation
- Vulnerability aggregation
- Email notifications

### 🔐 Unauthenticated APIs Report
**Location:** `unauthenticated-apis-report/`

Security automation tool that scans API endpoints to identify unauthenticated access vulnerabilities. Tests various HTTP methods and authentication schemes.

**Key Features:**
- Multi-method API testing (GET, POST, PUT, DELETE)
- Authentication bypass detection
- Token validation testing
- Automated security reporting
- Email notifications for vulnerabilities

## Getting Started

### Prerequisites
- Python 3.13+
- AWS CLI configured
- Appropriate cloud provider access
- Git for version control

### Quick Setup
```bash
# Clone the repository
git clone <repository-url>
cd devops-automation

# Navigate to specific solution (examples)
cd aws-cost-explorer-report
cd aws-cloudwatch-alarm-failed-monitoring
cd aws-iam-identity-accounts-sso
cd npm-vulnerability-report
cd kong-service-routes

# Follow solution-specific README
```

## Usage Guidelines

### For DevOps Teams
1. **Browse Solutions:** Each directory contains a specific automation solution
2. **Read Documentation:** Check individual README files for detailed instructions
3. **Customize:** Modify scripts according to your environment requirements
4. **Test:** Always test in non-production environments first
5. **Contribute:** Add new solutions following the established structure

### Security Best Practices
- Never commit actual credentials or sensitive data
- Use example files with placeholder values
- Implement proper secret management
- Follow least privilege access principles
- Regular security audits of automation scripts

## Contributing

### Adding New Solutions
1. Create a new directory with descriptive name
2. Include comprehensive README.md
3. Provide example configuration files
4. Add security considerations
5. Update this main README

### Directory Structure for New Solutions
```
solution-name/
├── README.md              # Detailed documentation
├── main-script.py         # Primary automation script
├── example-config.json    # Sample configuration
├── requirements.txt       # Dependencies (if applicable)
└── tests/                 # Test files (optional)
```

## Roadmap

### Planned Solutions
- [ ] Kubernetes cluster automation
- [ ] Terraform state management
- [ ] CI/CD pipeline templates
- [ ] Monitoring and alerting setup
- [ ] Container registry management
- [ ] Infrastructure cost optimization
- [ ] Backup and disaster recovery automation
- [ ] Multi-cloud resource management
- [ ] Security compliance automation

### Enhancement Areas
- [ ] Cross-cloud provider support
- [ ] Integration with popular DevOps tools
- [ ] Automated testing frameworks
- [ ] Performance monitoring
- [ ] Documentation automation

## Support & Maintenance

### Issue Reporting
- Use GitHub issues for bug reports
- Provide detailed reproduction steps
- Include environment information
- Tag issues appropriately

### Version Management
- Follow semantic versioning
- Maintain changelog for major updates
- Tag releases appropriately
- Document breaking changes

## License

This project is licensed under the MIT License - see individual solution directories for specific licensing information.

## Contact

**DevOps Lead:** Prashant Gupta

**Team:** Cloud Platform Lead

**Repository:** https://github.com/prashantgupta123/devops-automation

---

**Note:** This repository contains automation tools for DevOps operations. Always review and test scripts in non-production environments before deployment. Ensure compliance with your organization's security policies and procedures.