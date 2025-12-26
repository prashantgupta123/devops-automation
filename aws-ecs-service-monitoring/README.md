# AWS ECS Service Monitoring

Automated monitoring solution for AWS ECS services that detects service failures, deployment issues, and task placement problems. Sends real-time notifications via SNS and creates custom CloudWatch metrics for monitoring.

## Overview

This solution monitors ECS service events and automatically sends notifications when critical issues occur, including:
- Service task placement failures
- Service deployment failures  
- Task configuration issues
- Service discovery problems
- VPC Lattice target health issues

## Architecture

- **Lambda Function**: Processes ECS CloudWatch events and sends notifications
- **CloudWatch Event Rule**: Captures ECS service events and deployment state changes
- **SNS Topic**: Delivers notifications for critical events
- **Custom CloudWatch Metrics**: Tracks error event counts for monitoring

## Features

### 🔍 Event Monitoring
- **Service Task Placement Failure**: Insufficient CPU/memory or no available container instances
- **Service Task Configuration Failure**: ARN format or tagging issues
- **Service Daemon Placement Constraint Violated**: Placement constraint violations
- **ECS Operation Throttled**: API throttle limit issues
- **Service Discovery Operation Throttled**: AWS Cloud Map throttle limits
- **Service Deployment Failed**: Failed deployments with circuit breaker detection
- **Service Task Start Impaired**: Consistent task startup failures
- **Service Discovery Instance Unhealthy**: Unhealthy service registry tasks
- **VPC Lattice Target Unhealthy**: Unhealthy VPC Lattice targets

### 📊 Monitoring & Alerting
- Real-time SNS notifications with detailed event information
- Custom CloudWatch metrics (`ECSServiceErrorEventsCount`)
- Structured logging for troubleshooting
- Environment-specific alert subjects

## Prerequisites

- AWS CLI configured with appropriate permissions
- Terraform >= 1.14.3
- Python 3.x runtime for Lambda
- ECS clusters and services to monitor

## Required AWS Permissions

The Lambda function requires:
- `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`
- `sns:Publish` on the SNS topic
- `cloudwatch:PutMetricData`
- `ssm:GetParameter`
- EC2 network interface permissions for VPC access

## Configuration

### 1. Environment Configuration
Create configuration files:
- `config.yml` - Common project settings
- `config_default.yml` - Environment-specific settings

### 2. Workspace Configuration
```yaml
workspace:
  name: "your-workspace"
  sns:
    display_name: "ECS Service Monitoring"
    names: "ecs-service-alerts"
  lambda:
    app_name: "ecs-service-monitor"
    handler: "lambda_function.lambda_handler"
    runtime: "python3.9"
    timeout: 60
    memory_size: 128
    retention_in_days: 14
    cluster:
      cluster-name-1: ["service1", "service2"]
      cluster-name-2: ["service3", "service4"]
```

## Deployment

### Quick Deploy
```bash
# Make scripts executable
chmod +x launch.sh destroy.sh

# Deploy infrastructure
./launch.sh
# Enter environment: default

# Destroy infrastructure
./destroy.sh
# Enter environment: default
```

### Manual Deployment
```bash
# Initialize Terraform
terraform init

# Select workspace
terraform workspace select default

# Plan deployment
terraform plan

# Apply changes
terraform apply
```

## Monitored ECS Events

### Service Action Events
- `SERVICE_TASK_PLACEMENT_FAILURE`
- `SERVICE_TASK_CONFIGURATION_FAILURE`
- `SERVICE_DAEMON_PLACEMENT_CONSTRAINT_VIOLATED`
- `ECS_OPERATION_THROTTLED`
- `SERVICE_DISCOVERY_OPERATION_THROTTLED`
- `SERVICE_DEPLOYMENT_FAILED`
- `SERVICE_TASK_START_IMPAIRED`
- `SERVICE_DISCOVERY_INSTANCE_UNHEALTHY`
- `VPC_LATTICE_TARGET_UNHEALTHY`

### Deployment State Change Events
- `SERVICE_DEPLOYMENT_FAILED`

## Notification Format

```
Subject: [PROJECT_NAME] | [ENV] | ERROR: [Event Type]

Message:
Cluster Name: cluster-name
Service Name: service-name
Region: us-east-1
Event Name: SERVICE_TASK_PLACEMENT_FAILURE
Reason: [Event reason if available]
Message: [Detailed description]
```

## Custom Metrics

The solution creates custom CloudWatch metrics:
- **Namespace**: `AWS/ECS`
- **Metric Name**: `ECSServiceErrorEventsCount`
- **Dimensions**: `ClusterName`, `ServiceName`
- **Unit**: `Count`

## Troubleshooting

### Common Issues

1. **Lambda Function Not Triggering**
   - Verify CloudWatch Event Rule is enabled
   - Check ECS service ARNs in configuration
   - Ensure Lambda permissions are correct

2. **SNS Notifications Not Received**
   - Verify SNS topic subscription
   - Check Lambda execution logs
   - Validate SNS publish permissions

3. **Missing Events**
   - Confirm ECS services match configured ARN patterns
   - Check CloudWatch Event Rule pattern syntax
   - Verify service names in cluster configuration

### Logs and Monitoring
```bash
# View Lambda logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/your-function-name"

# Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name ECSServiceErrorEventsCount \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

## Security Considerations

- No hardcoded credentials in configuration files
- IAM roles follow least privilege principle
- Environment variables used for sensitive configuration
- VPC network interface permissions for secure access

## Cost Optimization

- Lambda function uses minimal memory (128MB)
- CloudWatch log retention set to 14 days
- Event-driven architecture minimizes compute costs
- Custom metrics reduce CloudWatch costs

## Contributing

1. Test changes in non-production environment
2. Update configuration examples
3. Add new event types to Lambda function
4. Update documentation for new features

## Support

For issues and questions:
- Check CloudWatch logs for Lambda execution details
- Verify ECS service configurations
- Review SNS topic subscriptions
- Validate IAM permissions

---

**Note**: This monitoring solution is designed for production ECS environments. Test thoroughly before deploying to critical systems.