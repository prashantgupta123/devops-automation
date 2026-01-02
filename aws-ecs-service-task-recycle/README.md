# AWS ECS Service Task Recycle

Automated Lambda function for recycling AWS ECS service tasks one by one, maintaining service availability during the process. Unlike ECS force deployment which replaces all tasks in parallel, this solution stops and replaces tasks sequentially with configurable wait times.

## Overview

This solution provides controlled task recycling for ECS services by:
- Stopping tasks one at a time instead of parallel replacement
- Waiting for service stability between each task replacement
- Optionally maintaining service state by temporarily increasing capacity
- Configurable wait time between task replacements

## Features

- **Sequential Task Recycling**: Stops and replaces tasks one by one
- **Service Stability**: Waits for stable state after each task replacement
- **Capacity Management**: Optional temporary capacity increase to maintain availability
- **Autoscaling Support**: Handles services with Application Auto Scaling
- **Flexible Authentication**: Multiple AWS credential methods via AWSSession module
- **Email Notifications**: Optional SMTP notifications on completion
- **CloudFormation Deployment**: Infrastructure as code with automated deployment
- **Zero Retries**: EventInvokeConfig set to 0 retry attempts
- **Comprehensive Logging**: Detailed CloudWatch logs for monitoring

## Architecture

```
Lambda Function (Python 3.13)
├── Event-driven execution
├── AWSSession.py (AWS authentication)
├── Notification.py (Email notifications)
└── input.json (Configuration)
```

## Prerequisites

- Python 3.13+
- AWS CLI configured
- IAM permissions for ECS and Application Auto Scaling
- SMTP server (optional, for notifications)

## Installation

### 1. Clone Repository
```bash
cd aws-ecs-service-task-recycle
```

### 2. Configure Settings
Edit `input.json` with your configuration:
```json
{
  "awsCredentials": {
    "region_name": "us-east-1"
  },
  "smtpCredentials": {
    "host": "smtp.example.com",
    "port": "587",
    "username": "user@example.com",
    "password": "password",
    "from_email": "noreply@example.com"
  },
  "emailNotification": {
    "email_subject": "ECS Service Task Recycle Completed",
    "subject_prefix": "AWS ECS",
    "to": ["admin@example.com"]
  }
}
```

### 3. Deploy CloudFormation Stack
```bash
chmod +x cloudformation_deploy.sh lambda_build.sh
./cloudformation_deploy.sh
```

## Usage

### Lambda Event Parameters

```json
{
  "cluster_name": "my-ecs-cluster",
  "service_name": "my-service",
  "maintain_service_state": true,
  "wait_time": 30
}
```

**Parameters:**
- `cluster_name` (required): ECS cluster name
- `service_name` (required): ECS service name
- `maintain_service_state` (optional, default: true): Temporarily increase capacity by 1
- `wait_time` (optional, default: 30): Seconds to wait between task replacements

### Invoke Lambda Function

**AWS CLI:**
```bash
aws lambda invoke \
  --function-name ecs-task-recycle-function \
  --payload '{"cluster_name":"my-cluster","service_name":"my-service","maintain_service_state":true,"wait_time":30}' \
  response.json
```

**AWS Console:**
1. Navigate to Lambda → Functions → ecs-task-recycle-function
2. Test tab → Create test event
3. Add event JSON and invoke

## How It Works

### Process Flow

1. **Get Current State**: Retrieve service configuration and running tasks
2. **Increase Capacity** (if maintain_service_state=true): Add +1 to desired count
3. **Wait for Stability**: Ensure new task is running
4. **Recycle Tasks**: For each old task:
   - Stop the task
   - Wait for replacement task to start
   - Wait for service stability
   - Sleep for configured wait_time
5. **Restore Capacity**: Return to original desired count
6. **Send Notification**: Email report (if configured)

### Example Scenario

**Service with 3 tasks:**
```
Initial State: 3 tasks running
↓
Increase to 4 tasks (maintain availability)
↓
Stop task 1 → Wait stable → Sleep 30s
↓
Stop task 2 → Wait stable → Sleep 30s
↓
Stop task 3 → Wait stable → Sleep 30s
↓
Restore to 3 tasks
↓
Complete
```

## Configuration

### AWS Credentials (input.json)

Multiple authentication methods supported:
```json
{
  "awsCredentials": {
    "region_name": "us-east-1",
    "profile_name": "my-profile",
    "role_arn": "arn:aws:iam::123456789012:role/MyRole",
    "access_key": "AKIAIOSFODNN7EXAMPLE",
    "secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
    "session_token": "token"
  }
}
```

### SMTP Configuration (Optional)

```json
{
  "smtpCredentials": {
    "host": "smtp.gmail.com",
    "port": "587",
    "username": "user@gmail.com",
    "password": "app-password",
    "from_email": "noreply@example.com"
  }
}
```

## IAM Permissions

Required permissions (included in CloudFormation):
```json
{
  "Effect": "Allow",
  "Action": [
    "ecs:DescribeServices",
    "ecs:UpdateService",
    "ecs:ListTasks",
    "ecs:StopTask",
    "ecs:DescribeTasks",
    "application-autoscaling:DescribeScalableTargets",
    "application-autoscaling:RegisterScalableTarget"
  ],
  "Resource": "*"
}
```

## CloudFormation Resources

- **Lambda Function**: Python 3.13 runtime, 900s timeout, 256MB memory
- **IAM Role**: Execution role with ECS and Auto Scaling permissions
- **EventInvokeConfig**: MaximumRetryAttempts set to 0
- **CloudWatch Logs**: 7-day retention

## Monitoring

### CloudWatch Logs
```bash
aws logs tail /aws/lambda/ecs-task-recycle-function --follow
```

### Key Log Messages
- `Starting task recycle for {cluster}/{service}`
- `Original desired count: X, tasks: Y`
- `Recycling task N/M: {task_arn}`
- `Task N recycled, waiting Xs`
- `Task recycle completed successfully`

## Troubleshooting

### Service Not Stabilizing
- Increase waiter MaxAttempts in code (default: 40)
- Check ECS service health and task definitions
- Verify target group health checks

### Timeout Errors
- Increase Lambda timeout (default: 900s)
- Reduce number of tasks or increase wait_time

### Authentication Failures
- Verify IAM role permissions
- Check AWS credentials in input.json
- Ensure Lambda execution role is correct

## Best Practices

1. **Test in Non-Production**: Always test with non-critical services first
2. **Monitor CloudWatch**: Watch logs during first execution
3. **Adjust Wait Time**: Tune based on application startup time
4. **Use Maintain State**: Enable for production services
5. **Schedule Wisely**: Run during low-traffic periods

## Comparison with Force Deployment

| Feature | Force Deployment | Task Recycle |
|---------|-----------------|--------------|
| Task Replacement | Parallel | Sequential |
| Service Disruption | Higher | Lower |
| Completion Time | Faster | Slower |
| Control | Limited | Configurable |
| Wait Between Tasks | No | Yes |

## Security Considerations

- Lambda execution role follows least privilege
- No hardcoded credentials in code
- SMTP credentials stored in input.json (use Secrets Manager in production)
- CloudWatch logs for audit trail
- EventInvokeConfig prevents retry storms

## Cost Optimization

- Lambda execution time: ~(number_of_tasks × wait_time) seconds
- CloudWatch Logs: 7-day retention
- No additional AWS service costs
- Consider scheduling during off-peak hours

## Limitations

- Maximum Lambda execution time: 15 minutes
- Suitable for services with < 20 tasks (with 30s wait time)
- Requires stable service for waiter to succeed
- No rollback mechanism on failure

## Contributing

Contributions welcome! Please follow the repository structure:
1. Test changes thoroughly
2. Update documentation
3. Follow existing code style
4. Add error handling

## License

MIT License - See repository root for details

## Support

For issues or questions:
- Check CloudWatch logs first
- Review IAM permissions
- Verify ECS service health
- Contact DevOps team

## Version History

- **v1.0.0**: Initial release with sequential task recycling
  - Event-driven Lambda function
  - AWSSession and Notification integration
  - CloudFormation deployment
  - Zero retry configuration

---

**Author**: DevOps Team  
**Last Updated**: 2024
