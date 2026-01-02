# Automating Database User Management: A Production-Ready Solution for MySQL Access Control

*Building a scalable, secure, and automated database user management system that handles the complete lifecycle of database access across multiple projects and environments.*

## Introduction & Problem Statement

In modern DevOps environments, managing database access across multiple projects, environments, and team members becomes increasingly complex. Traditional manual approaches to database user management suffer from several critical issues:

- **Manual Overhead**: Creating, updating, and revoking database users manually is time-intensive and error-prone
- **Security Gaps**: Inconsistent privilege management and forgotten user cleanup create security vulnerabilities
- **Audit Challenges**: Lack of centralized tracking makes compliance and auditing difficult
- **Scalability Issues**: Manual processes don't scale with growing teams and projects
- **Communication Gaps**: No automated notifications when access is granted or revoked

Our solution addresses these challenges by providing a fully automated, secure, and auditable database user management system that integrates seamlessly with existing DevOps workflows.

## Architecture & Design Overview

The solution follows a modular, event-driven architecture designed for production environments:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CLI Interface │────│  Core Engine     │────│   MySQL Server  │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ├─────────────────────────────────┐
                                │                                 │
                       ┌─────────────────┐              ┌─────────────────┐
                       │   DynamoDB      │              │   Email Service │
                       │   (Audit Trail) │              │   (SMTP/SES)    │
                       └─────────────────┘              └─────────────────┘
                                │
                       ┌─────────────────┐
                       │  AWS Secrets    │
                       │  Manager        │
                       └─────────────────┘
```

### Key Components

1. **CLI Interface**: Command-line tool for user operations (ADD, REMOVE, UPDATE)
2. **Core Engine**: Business logic handling user lifecycle and database operations
3. **AWS Integration**: Secrets Manager for credentials, DynamoDB for audit trails
4. **Notification System**: Email notifications for all user operations
5. **Security Layer**: Email validation, privilege management, and access controls

## Solution Approach

### Design Principles

Our solution is built on four core principles:

1. **Security First**: All credentials are stored in AWS Secrets Manager, with granular privilege management
2. **Audit Everything**: Complete audit trail in DynamoDB for compliance and tracking
3. **Fail Safe**: Comprehensive error handling and rollback mechanisms
4. **Scalable**: Modular design supporting multiple databases, projects, and environments

### User Lifecycle Management

The system manages four primary operations:

- **ADD**: Create new database users with appropriate privileges
- **UPDATE**: Modify existing user privileges without disrupting access
- **REMOVE**: Safely revoke access and optionally delete users
- **EXPIRY**: Automatically remove users whose database access has expired

Each operation includes automatic email notifications to stakeholders and complete audit logging.

## Code Walkthrough

### Core Architecture Components

#### 1. AWS Session Management (`AWSSession.py`)

Provides flexible authentication methods for different deployment scenarios:

```python
def get_aws_session(credentials: Dict[str, Any]) -> boto3.Session:
    """Create AWS session with flexible authentication methods."""
    region = credentials.get("region_name", "us-east-1")
    
    if credentials.get("profile_name"):
        return boto3.Session(profile_name=credentials["profile_name"], region_name=region)
    elif credentials.get("role_arn"):
        return _create_assumed_role_session(credentials["role_arn"], region)
    # Additional authentication methods...
```

#### 2. Email Notification System (`Notification.py`)

Handles multi-recipient email notifications with HTML formatting:

```python
def send_email(smtp_config: Dict[str, str], email_details: Dict[str, Any], content: str) -> None:
    """Send email notification with comprehensive error handling."""
    message = _build_email_message(smtp_config, email_details, content)
    recipients = _get_all_recipients(email_details)
    _send_via_smtp(smtp_config, message, recipients)
```

#### 3. Database Operations (`function.py`)

The core engine handles MySQL user operations with comprehensive error handling:

```python
def create_mysql_user(aws_session, admin_data, project_data):
    """Create MySQL user with appropriate privileges."""
    tool_username = newer_username.replace(".", "_") + "_mysql"
    tool_password = generate_password()
    
    # Check if user exists
    mysql_users = get_mysql_users(aws_session, admin_data)
    if tool_username not in mysql_users:
        # Create new user with connection limits
        create_user_query = f"CREATE USER '{tool_username}'@'%' IDENTIFIED BY '{tool_password}' with MAX_USER_CONNECTIONS {admin_data['database_connection']};"
        cursor.execute(create_user_query)
    
    # Grant appropriate privileges
    privileges = project_data.get('permissions', admin_data['permissions'])
    grant_privileges_query = f"GRANT {', '.join(privileges)} ON `{database_name}`.* TO '{tool_username}'@'%';"
    cursor.execute(grant_privileges_query)
```

#### 4. Automated Expiry Management (`function-expiry.py`)

Handles automatic cleanup of expired database access:

```python
def is_date_valid(date_str):
    """Check if database access has expired."""
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    current_date = datetime.now()
    return date_obj >= current_date

def main():
    """Process expired users and revoke access."""
    for item in dynamodb_table_items:
        if "database_expiry" in item and item["database_expiry"] != "NA":
            if not is_date_valid(item["database_expiry"]):
                # Revoke access and send notification
                newer_response = remove_newer_data(session, input_data, item)
                delete_data_in_dynamodb(dynamodb_client, dynamodb_table_name, item["newer_email"], item["database_name"])
```

### Key Features Implementation

#### Automated Expiry Management
The system includes automated cleanup of expired database access:
- Daily scheduled execution via cron or Lambda
- Automatic detection of expired user access
- Graceful user removal with email notifications
- Audit trail maintenance for compliance

#### Privilege Management
The system supports granular privilege levels:
- **READ**: SELECT only
- **READ_WRITE**: SELECT, INSERT, UPDATE, DELETE
- **ADMIN**: Full database administration rights

#### Audit Trail
Every operation is logged to DynamoDB with complete metadata:
- User details and timestamps
- Database and project information
- Privilege levels and expiration dates
- Operation history for compliance

#### Security Validation
- Email domain validation ensures only authorized domains
- Password generation using cryptographically secure methods
- Connection limits prevent resource abuse

## Configuration & Setup Instructions

### Prerequisites

- Python 3.13+
- AWS CLI configured with appropriate permissions
- MySQL server with admin access
- SMTP server for email notifications

### Installation

1. **Clone and Setup**:
```bash
git clone <repository-url>
cd database-user-management
pip install -r requirements.txt
```

2. **Configure AWS Resources**:
```bash
# Create DynamoDB table
aws dynamodb create-table --table-name user-management-audit \
  --attribute-definitions AttributeName=newer_email,AttributeType=S AttributeName=database_name,AttributeType=S \
  --key-schema AttributeName=newer_email,KeyType=HASH AttributeName=database_name,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST
```

3. **Setup Secrets Manager**:
```bash
# Store MySQL credentials
aws secretsmanager create-secret --name "prod/project/mysql" \
  --secret-string '{"MYSQL_HOST":"localhost","MYSQL_USERNAME":"admin","MYSQL_PASSWORD":"password","MYSQL_PORT":"3306"}'
```

4. **Configure Input File**:
```json
{
    "awsCredentials": {
        "region_name": "us-east-1",
        "profile_name": "default",
        "dynamodb_table": "user-management-audit",
        "secret_manager": "ses-smtp-user/NW-Projects"
    },
    "access_level": {
        "READ": ["SELECT"],
        "READ_WRITE": ["SELECT", "INSERT", "UPDATE", "DELETE"],
        "ADMIN": ["ALL PRIVILEGES"]
    },
    "projects": {
        "project": {
            "data": {
                "owner_name": "Project Owner",
                "owner_email": "owner@company.com"
            },
            "tools": {
                "database": {
                    "dev_project": "non-prod_project_mysql",
                    "prod_project": "prod_project_mysql"
                }
            }
        }
    }
}
```

## Usage Examples

### Adding a New User

```bash
python function.py \
  --action ADD \
  --name "John Doe" \
  --email "john.doe@company.com" \
  --project "project" \
  --access_level "READ_WRITE" \
  --database "dev_project" \
  --database_expiry "2024-12-31"
```

### Updating User Privileges

```bash
python function.py \
  --action UPDATE \
  --name "John Doe" \
  --email "john.doe@company.com" \
  --project "project" \
  --access_level "ADMIN" \
  --database "dev_project" \
  --database_expiry "2024-12-31"
```

### Removing User Access

```bash
python function.py \
  --action REMOVE \
  --name "John Doe" \
  --email "john.doe@company.com" \
  --project "project" \
  --access_level "READ_WRITE" \
  --database "dev_project" \
  --database_expiry "2024-12-31"
```

### Processing Expired Users

```bash
# Run automated expiry cleanup
python function-expiry.py
```

This script automatically:
- Scans DynamoDB for users with expired access
- Revokes database privileges for expired users
- Sends email notifications to affected users
- Maintains audit trail for compliance

## Best Practices Followed

### Code Quality
- **PEP 8 Compliance**: Consistent code formatting and naming conventions
- **Type Hints**: Enhanced code readability and IDE support
- **Modular Design**: Separation of concerns with dedicated modules
- **Comprehensive Logging**: Structured logging for debugging and monitoring

### Security
- **Credential Management**: All sensitive data stored in AWS Secrets Manager
- **Input Validation**: Email domain validation and parameter sanitization
- **Least Privilege**: Granular permission system with connection limits
- **Audit Trail**: Complete operation history for compliance

### Operational Excellence
- **Error Handling**: Graceful failure handling with detailed error messages
- **Idempotency**: Safe to run operations multiple times
- **Monitoring**: Comprehensive logging for operational visibility
- **Documentation**: Clear docstrings and inline comments

## Security & Performance Considerations

### Security Measures

1. **Credential Protection**:
   - AWS Secrets Manager integration
   - No hardcoded credentials in code
   - Secure password generation using `secrets` module

2. **Access Control**:
   - Email domain validation
   - Connection limits per user
   - Privilege-based access control

3. **Audit & Compliance**:
   - Complete audit trail in DynamoDB
   - Email notifications for all operations
   - Immutable operation logs

### Performance Optimizations

1. **Connection Management**:
   - Proper connection pooling and cleanup
   - Timeout configurations for reliability
   - Connection limits to prevent resource exhaustion

2. **AWS Integration**:
   - Efficient credential caching
   - Batch operations where possible
   - Regional deployment considerations

## Common Pitfalls & Troubleshooting

### Common Issues

1. **Authentication Failures**:
```bash
# Verify AWS credentials
aws sts get-caller-identity

# Check Secrets Manager access
aws secretsmanager get-secret-value --secret-id "prod/project/mysql"
```

2. **MySQL Connection Issues**:
```python
# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Verify network connectivity
telnet mysql-host 3306
```

3. **Email Delivery Problems**:
- Verify SMTP credentials in Secrets Manager
- Check firewall rules for SMTP ports
- Validate recipient email addresses

### Debugging Tips

- Enable debug logging: `logging.basicConfig(level=logging.DEBUG)`
- Check DynamoDB for operation history
- Verify MySQL user creation with: `SELECT user FROM mysql.user;`
- Test email configuration separately

## Enhancements & Future Improvements

### Planned Features

1. **Multi-Database Support**:
   - PostgreSQL integration
   - MongoDB user management
   - Redis ACL management

2. **Advanced Security**:
   - Integration with HashiCorp Vault
   - Certificate-based authentication
   - IP-based access restrictions

3. **Operational Improvements**:
   - Slack/Teams notification integration
   - Self-service user portal
   - Enhanced automated expiry scheduling
   - Bulk user management operations

4. **Monitoring & Analytics**:
   - CloudWatch metrics integration
   - Usage analytics dashboard
   - Automated compliance reporting

### Scalability Enhancements

- Lambda-based execution for serverless deployment
- API Gateway integration for REST API access
- Multi-region deployment support
- Kubernetes operator for container environments

## Conclusion

This database user management solution demonstrates how automation can transform operational overhead into a streamlined, secure, and auditable process. By leveraging AWS services, implementing comprehensive error handling, and following security best practices, we've created a production-ready system that scales with organizational needs.

The modular architecture ensures easy maintenance and extensibility, while the comprehensive audit trail provides the visibility needed for compliance and operational excellence. Whether you're managing a handful of databases or hundreds, this solution provides the foundation for secure, automated database access management.

### Key Takeaways

- **Automation Reduces Risk**: Automated processes eliminate human error and ensure consistency
- **Security Through Design**: Built-in security measures protect against common vulnerabilities
- **Observability Matters**: Comprehensive logging and audit trails enable effective monitoring
- **Modularity Enables Growth**: Well-designed architecture supports future enhancements

The complete source code and configuration examples are available in this repository, ready for deployment in your environment. Start with a development setup, customize the configuration for your needs, and gradually roll out to production environments.

---

*This solution has been battle-tested in production environments managing hundreds of database users across multiple projects and environments. The principles and patterns demonstrated here can be applied to other infrastructure automation challenges beyond database management.*