# Automated EC2 Instance Scheduling: A Cost-Optimized Approach to Managing Non-Production Workloads

## Introduction & Problem Statement

In cloud environments, cost optimization is a critical concern for engineering teams. One of the most straightforward yet impactful strategies is scheduling non-production EC2 instances to run only during business hours. Consider a typical scenario:

- **Development/Any environments** running 24/7 unnecessarily
- **Monthly cost**: ~$730 per instance (assuming $1/hour)
- **Actual usage**: Only 12 hours/day, 5 days/week (~60 hours/week)
- **Potential savings**: Up to 64% reduction in compute costs

However, manually starting and stopping instances is error-prone, time-consuming, and doesn't scale. Teams need an automated, reliable, and auditable solution that:

1. **Schedules instances** based on business hours
2. **Supports multiple modules** (backend, frontend, databases)
3. **Provides notifications** for visibility and troubleshooting
4. **Integrates with existing infrastructure** (VPC, security groups, IAM)
5. **Maintains high availability** during operational hours

This article presents a production-ready solution using AWS Lambda, EventBridge, Terraform, and SNS to automate EC2 instance lifecycle management with enterprise-grade reliability.

## Architecture & Design Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     EventBridge Scheduler                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Start Event  │  │ Stop Event   │  │ Start Event  │          │
│  │ (06:00 UTC)  │  │ (18:00 UTC)  │  │ (06:00 UTC)  │  ...     │
│  │ Backend      │  │ Backend      │  │ Frontend     │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             ▼
                  ┌──────────────────────┐
                  │   Lambda Function    │
                  │  (VPC-enabled)       │
                  │  - Validate Event    │
                  │  - Start/Stop EC2    │
                  │  - Send Notification │
                  └──────────┬───────────┘
                             │
                ┌────────────┼────────────┐
                ▼            ▼            ▼
         ┌──────────┐  ┌─────────┐  ┌─────────┐
         │   EC2    │  │   SNS   │  │ CloudW. │
         │ Instances│  │  Topic  │  │  Logs   │
         └──────────┘  └─────────┘  └─────────┘
```

### Key Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| **EventBridge Rules** | Schedule-based triggers for start/stop operations | AWS EventBridge (Cron) |
| **Lambda Function** | Orchestrates EC2 operations and notifications | Python 3.14 Runtime |
| **SNS Topic** | Delivers success/failure notifications | AWS SNS |
| **IAM Role** | Grants Lambda permissions for EC2, SNS, VPC | AWS IAM |
| **Security Group** | Controls Lambda network access | AWS VPC |
| **CloudWatch Logs** | Centralized logging and monitoring | AWS CloudWatch |
| **CloudWatch Alarms** | Alerts on Lambda errors | AWS CloudWatch Alarms |
| **Terraform** | Infrastructure as Code for deployment | Terraform 1.14+ |

### Design Principles

1. **Event-Driven Architecture**: EventBridge triggers Lambda based on cron schedules
2. **Idempotency**: Safe to retry; starting an already-running instance is a no-op
3. **Fail-Fast Validation**: Input validation before AWS API calls
4. **Observability**: Comprehensive logging and SNS notifications
5. **Security**: VPC-enabled Lambda, least-privilege IAM, no hardcoded credentials
6. **Infrastructure as Code**: Fully automated deployment via Terraform

## Solution Approach

### Workflow

The solution follows a straightforward event-driven workflow:

1. **EventBridge Trigger**: Cron expression fires at scheduled time (e.g., 06:00 UTC)
2. **Event Payload**: Contains action (`start`/`stop`), module name, and instance details
3. **Lambda Invocation**: Function receives event and validates parameters
4. **EC2 Operation**: Calls `start_instances()` or `stop_instances()` API
5. **Notification**: Publishes success/failure message to SNS topic
6. **Logging**: All operations logged to CloudWatch for audit trail

### Event Structure

Each EventBridge rule sends a structured JSON payload:

```json
{
  "action": "start",
  "module": "backendserver",
  "instance_details": {
    "i-11223344556677889": "test-prod-backendserver"
  }
}
```

This design allows:
- **Multiple instances** per event (batch operations)
- **Module-based grouping** for logical separation
- **Descriptive naming** for better observability

### Scheduling Strategy

The solution uses cron expressions for precise scheduling:

```
Start:  cron(0 6 ? * MON-FRI *)   # 06:00 AM UTC, weekdays only
Stop:   cron(0 18 ? * MON-FRI *)  # 06:00 PM UTC, weekdays only
```

This ensures:
- **Cost savings** during nights and weekends
- **Availability** during business hours
- **Flexibility** to customize per module

## Code Walkthrough

### Lambda Function Architecture

The refactored Lambda function follows object-oriented principles with clear separation of concerns:

#### 1. EC2InstanceManager Class

Encapsulates EC2 operations with clean interfaces:

```python
class EC2InstanceManager:
    def start_instances(self, instance_ids: List[str]) -> Dict[str, Any]:
        logger.info(f"Starting instances: {instance_ids}")
        return self.ec2.start_instances(InstanceIds=instance_ids)

    def stop_instances(self, instance_ids: List[str]) -> Dict[str, Any]:
        logger.info(f"Stopping instances: {instance_ids}")
        return self.ec2.stop_instances(InstanceIds=instance_ids)
```

**Benefits**:
- Single responsibility (EC2 operations only)
- Easy to mock for unit testing
- Reusable across different contexts

#### 2. NotificationService Class

Handles SNS publishing with intelligent message formatting:

```python
class NotificationService:
    def send_notification(
        self, action: str, module: str, 
        instance_details: Dict[str, str],
        status: str = "INFO",
        error_message: Optional[str] = None
    ) -> None:
        subject = f"{self.subject_prefix} | {status} | {action.upper()} - {module}"
        # Format message based on success/failure
        self.sns.publish(TopicArn=self.topic_arn, Subject=subject, Message=message)
```

**Benefits**:
- Consistent notification format
- Graceful handling of missing SNS configuration
- Error notifications for troubleshooting

#### 3. Event Validation

Fail-fast validation prevents unnecessary AWS API calls:

```python
def validate_event(event: Dict[str, Any]) -> tuple[str, str, Dict[str, str]]:
    if action not in ['start', 'stop']:
        raise ValueError(f"Invalid action: '{action}'")
    if not instance_details or not isinstance(instance_details, dict):
        raise ValueError("Missing or invalid 'instance_details'")
    return action, module, instance_details
```

**Benefits**:
- Clear error messages for debugging
- Prevents partial operations
- Returns 400 status for client errors

#### 4. Lambda Handler

Orchestrates the entire workflow with comprehensive error handling:

```python
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        action, module, instance_details = validate_event(event)
        
        if action == 'start':
            response = instance_manager.start_instances(instance_ids)
        else:
            response = instance_manager.stop_instances(instance_ids)
        
        notification_service.send_notification(...)
        return {'statusCode': 200, 'body': json.dumps({...})}
    
    except ValueError as e:
        return {'statusCode': 400, 'body': json.dumps({'error': str(e)})}
    except (ClientError, BotoCoreError) as e:
        notification_service.send_notification(..., status="ERROR")
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
```

**Benefits**:
- Structured error handling (400 vs 500)
- Automatic failure notifications
- Detailed logging for troubleshooting

### Terraform Infrastructure

The Terraform configuration provisions all required AWS resources:

#### Key Resources

1. **Lambda Function** with VPC configuration
2. **IAM Role** with EC2, SNS, and VPC permissions
3. **Security Group** for Lambda network access
4. **EventBridge Rules** for each start/stop schedule
5. **SNS Topic** for notifications
6. **CloudWatch Log Group** with retention policy
7. **CloudWatch Alarms** for error monitoring

#### Workspace-Based Configuration

The solution uses Terraform workspaces for environment separation:

```
workspace_prod_ap-south-1.yml  # Production configuration
workspace.yml                   # Common configuration
```

This enables:
- **Multi-environment support** (dev, staging, prod)
- **Region-specific settings**
- **Environment-specific schedules**

## Configuration & Setup Instructions

### Prerequisites

- **AWS Account** with appropriate permissions
- **Terraform** 1.14.3 or higher
- **AWS CLI** configured with credentials
- **S3 Bucket** for Terraform state (e.g., `test-infra-terraform`)
- **VPC** with private subnets
- **SNS Topic** (optional, created automatically)

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd devops-automation/aws-start-stop-services
```

### Step 2: Configure Workspace

Edit `workspace_prod_ap-south-1.yml` with your environment details:

```yaml
workspace:
  aws:
    account_id: "123456789012"        # Your AWS account ID
    region: "ap-south-1"               # Target region
    vpc:
      id: "vpc-xxxxx"                  # VPC ID
      subnet_ids:
        private: ["subnet-xxx", ...]   # Private subnet IDs

  event:
    start-backendserver:
      schedule_expression: "cron(0 6 ? * MON-FRI *)"
      event_input:
        action: "start"
        module: "backendserver"
        instance_details:
          "i-xxxxx": "instance-name"   # Your instance ID and name
```

### Step 3: Update Backend Configuration

Edit `aws.tf` to match your S3 bucket:

```hcl
terraform {
  backend "s3" {
    bucket  = "your-terraform-state-bucket"
    key     = "project/app/lambda/start-stop-services/main.tfstate"
    region  = "ap-south-1"
    encrypt = true
  }
}
```

### Step 4: Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Select workspace
terraform workspace select prod_ap-south-1 || terraform workspace new prod_ap-south-1

# Review plan
terraform plan

# Apply configuration
terraform apply
```

Or use the provided script:

```bash
chmod +x launch.sh
./launch.sh
# Enter: prod_ap-south-1
```

### Step 5: Verify Deployment

```bash
# Check Lambda function
aws lambda get-function --function-name prod-project-start-stop-lambda

# Check EventBridge rules
aws events list-rules --name-prefix prod-project

# Check SNS topic
aws sns list-topics | grep start-stop-lambda
```

## Usage Examples

### Manual Lambda Invocation

Test the Lambda function manually:

```bash
# Start instances
aws lambda invoke \
  --function-name prod-project-start-stop-lambda \
  --payload '{
    "action": "start",
    "module": "backendserver",
    "instance_details": {
      "i-11223344556677889": "test-prod-backendserver"
    }
  }' \
  response.json

# Check response
cat response.json
```

### Scheduled Execution

EventBridge automatically triggers the Lambda function based on cron schedules:

- **06:00 AM UTC (Mon-Fri)**: Start backend and frontend servers
- **06:00 PM UTC (Mon-Fri)**: Stop backend and frontend servers

### SNS Notifications

Subscribers receive email notifications:

**Success Notification:**
```
Subject: MyProject | [LAMBDA Notification] | INFO | START - backendserver

Hi,

Successfully started instances for module 'backendserver'

Instance Details:
{
  "i-11223344556677889": "test-prod-backendserver"
}
```

**Failure Notification:**
```
Subject: MyProject | [LAMBDA Notification] | ERROR | START FAILED - backendserver

Error: An error occurred (InvalidInstanceID.NotFound) when calling the StartInstances operation

Module: backendserver
Action: start
Instances: ['i-11223344556677889']
```

### CloudWatch Logs

View execution logs:

```bash
aws logs tail /aws/lambda/prod-project-start-stop-lambda --follow
```

## Best Practices Followed

### 1. Infrastructure as Code

- **Terraform** for reproducible deployments
- **Version control** for all configuration
- **Workspace isolation** for environments

### 2. Security

- **VPC-enabled Lambda** for network isolation
- **Least-privilege IAM** with specific resource permissions
- **No hardcoded credentials** (environment variables only)
- **Encrypted S3 backend** for Terraform state

### 3. Observability

- **Structured logging** with log levels
- **SNS notifications** for all operations
- **CloudWatch alarms** for error detection
- **30-day log retention** for compliance

### 4. Code Quality

- **PEP 8 compliance** for Python code
- **Type hints** for better IDE support
- **Docstrings** for all functions and classes
- **Error handling** with specific exception types
- **Modular design** with single-responsibility classes

### 5. Reliability

- **Event invoke config** with 0 retries (idempotent operations)
- **Input validation** before AWS API calls
- **Graceful error handling** with appropriate status codes
- **Timeout configuration** (300 seconds)

### 6. Cost Optimization

- **Right-sized Lambda** (512 MB memory)
- **VPC endpoints** for S3 access (no NAT gateway charges)
- **Log retention policy** (30 days)
- **Scheduled execution** only during business hours

## Security & Performance Considerations

### Security

#### IAM Permissions

The Lambda function uses least-privilege permissions:

```json
{
  "Effect": "Allow",
  "Action": [
    "ec2:StartInstances",
    "ec2:StopInstances",
    "ec2:DescribeInstances"
  ],
  "Resource": "*"
}
```

**Recommendation**: Restrict to specific instance IDs using resource-based policies:

```json
{
  "Resource": "arn:aws:ec2:ap-south-1:123456789012:instance/i-*"
}
```

#### Network Security

- **VPC-enabled Lambda** prevents public internet access
- **Security group** allows only HTTPS egress
- **VPC endpoints** for S3 and SSM (no internet gateway required)

#### Secrets Management

- **SNS topic ARN** passed via environment variables
- **No credentials** in code or configuration files
- **AWS SDK** uses IAM role credentials automatically

### Performance

#### Lambda Configuration

- **Memory**: 512 MB (sufficient for boto3 operations)
- **Timeout**: 300 seconds (handles multiple instances)
- **Runtime**: Python 3.14 (latest stable version)

#### Optimization Strategies

1. **Reuse boto3 clients** (initialized outside handler)
2. **Batch operations** (multiple instances per invocation)
3. **Async notifications** (don't block on SNS publish)
4. **VPC endpoints** (reduce latency for AWS API calls)

#### Scaling Considerations

- **Concurrent executions**: Default limit (1000)
- **EventBridge rules**: No limit on number of schedules
- **Instance limit**: Tested with up to 50 instances per event

## Common Pitfalls & Troubleshooting

### Issue 1: Lambda Timeout

**Symptom**: Function times out after 300 seconds

**Cause**: Too many instances in a single event

**Solution**: Split into multiple EventBridge rules or increase timeout

```yaml
lambda:
  timeout: 600  # Increase to 10 minutes
```

### Issue 2: VPC Connectivity

**Symptom**: `Unable to connect to endpoint` errors

**Cause**: Missing VPC endpoints or incorrect security group

**Solution**: Verify VPC endpoints and security group rules

```bash
# Check VPC endpoints
aws ec2 describe-vpc-endpoints --filters "Name=vpc-id,Values=vpc-xxxxx"

# Verify security group allows HTTPS egress
aws ec2 describe-security-groups --group-ids sg-xxxxx
```

### Issue 3: Permission Denied

**Symptom**: `AccessDeniedException` or `UnauthorizedOperation`

**Cause**: Insufficient IAM permissions

**Solution**: Verify IAM role has required permissions

```bash
# Test IAM permissions
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::123456789012:role/lambda-role \
  --action-names ec2:StartInstances ec2:StopInstances
```

### Issue 4: Instance Not Found

**Symptom**: `InvalidInstanceID.NotFound` error

**Cause**: Incorrect instance ID in configuration

**Solution**: Verify instance IDs exist in the target region

```bash
# List instances
aws ec2 describe-instances --instance-ids i-xxxxx
```

### Issue 5: SNS Notifications Not Received

**Symptom**: No email notifications

**Cause**: SNS subscription not confirmed or topic ARN incorrect

**Solution**: Confirm SNS subscription and verify topic ARN

```bash
# List subscriptions
aws sns list-subscriptions-by-topic --topic-arn arn:aws:sns:...

# Verify environment variable
aws lambda get-function-configuration \
  --function-name prod-project-start-stop-lambda \
  --query 'Environment.Variables.SNS_TOPIC_ARN'
```

## Enhancements & Future Improvements

### Short-Term Enhancements

1. **Dynamic Scheduling**
   - Store schedules in DynamoDB
   - Update schedules without redeployment
   - Per-instance custom schedules

2. **Cost Reporting**
   - Calculate actual savings
   - Send weekly cost reports
   - Compare with 24/7 baseline

3. **Health Checks**
   - Verify instance state after start/stop
   - Retry failed operations
   - Alert on persistent failures

4. **Multi-Region Support**
   - Replicate across regions
   - Centralized configuration
   - Cross-region reporting

### Long-Term Improvements

1. **Auto Scaling Integration**
   - Coordinate with Auto Scaling groups
   - Suspend/resume scaling policies
   - Maintain desired capacity

2. **RDS Support**
   - Start/stop RDS instances
   - Snapshot before stop
   - Multi-AZ considerations

3. **ECS/EKS Support**
   - Scale ECS services to 0
   - Stop EKS node groups
   - Preserve task definitions

4. **Self-Service Portal**
   - Web UI for schedule management
   - Role-based access control
   - Audit trail and approval workflow

5. **Machine Learning**
   - Predict optimal schedules based on usage
   - Anomaly detection for unexpected usage
   - Automatic schedule adjustments

### Code Improvements

1. **Unit Tests**
   - Mock boto3 clients
   - Test error scenarios
   - Validate event parsing

2. **Integration Tests**
   - End-to-end workflow testing
   - SNS notification verification
   - CloudWatch log validation

3. **CI/CD Pipeline**
   - Automated testing
   - Terraform plan on PR
   - Automated deployment

## Conclusion

Automated EC2 instance scheduling is a simple yet powerful cost optimization strategy that can reduce non-production compute costs by up to 64%. This solution provides:

✅ **Production-ready code** with comprehensive error handling  
✅ **Infrastructure as Code** for reproducible deployments  
✅ **Enterprise-grade security** with VPC and IAM best practices  
✅ **Full observability** with logging and notifications  
✅ **Flexible scheduling** with EventBridge cron expressions  
✅ **Scalable architecture** supporting multiple modules and instances  

### Key Takeaways

1. **Event-driven architecture** simplifies scheduling logic
2. **Terraform workspaces** enable multi-environment management
3. **SNS notifications** provide visibility without manual monitoring
4. **VPC-enabled Lambda** maintains security without sacrificing functionality
5. **Modular Python code** improves maintainability and testability

### Getting Started

1. Clone the repository
2. Configure your environment in `workspace_prod_ap-south-1.yml`
3. Run `./launch.sh` to deploy
4. Monitor CloudWatch logs and SNS notifications
5. Iterate on schedules based on actual usage patterns

### Cost Impact

For a typical setup with 10 EC2 instances:

- **Before**: 10 instances × 24 hours × 30 days × $1/hour = **$7,200/month**
- **After**: 10 instances × 12 hours × 22 days × $1/hour = **$2,640/month**
- **Savings**: **$4,560/month (63% reduction)**

The Lambda function costs are negligible (~$0.20/month for 1,000 invocations).

### Resources

- **AWS Lambda**: https://aws.amazon.com/lambda/
- **EventBridge**: https://aws.amazon.com/eventbridge/
- **Terraform**: https://www.terraform.io/
- **Boto3 Documentation**: https://boto3.amazonaws.com/v1/documentation/api/latest/index.html

---

**Author**: Prashant Gupta | Cloud Platform Lead  
**Repository**: [devops-automation](https://github.com/prashantgupta123/devops-automation)  
**License**: MIT 

**Questions or feedback?** Open an issue or submit a pull request!
