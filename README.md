# DevOps Automation Solutions

A comprehensive collection of DevOps automation tools and scripts for cloud infrastructure management, CI/CD pipelines, and operational tasks.

## Repository Structure

```
devops-automation/
├── aws-cost-explorer-report/         # AWS cost analysis and reporting
├── aws-cw-orphan-alarms/            # CloudWatch orphaned alarms cleanup
├── aws-ec2-backup-check/            # EC2 backup validation automation
├── aws-iam-identity-accounts-sso/   # AWS SSO credential automation
├── aws-news/                        # AWS news aggregation service
├── aws-target-group-report/         # Target group health reporting
├── npm-vulnerability-report/        # NPM security vulnerability scanning
├── unauthenticated-apis-report/     # API authentication security scanning
└── README.md                        # This file
```

## Solutions Overview

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

### 💾 AWS EC2 Backup Check
**Location:** `aws-ec2-backup-check/`

Validates EC2 instance backup compliance and sends notifications for instances without proper backup configurations. Deployable as Lambda function.

**Key Features:**
- Automated backup validation
- CloudFormation deployment
- Email notifications via SES
- Scheduled execution support

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
cd aws-iam-identity-accounts-sso
cd npm-vulnerability-report
cd unauthenticated-apis-report

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

**DevOps Lead:** [Your Name]
**Team:** DevOps Engineering
**Repository:** [Repository URL]

---

**Note:** This repository contains automation tools for DevOps operations. Always review and test scripts in non-production environments before deployment. Ensure compliance with your organization's security policies and procedures.