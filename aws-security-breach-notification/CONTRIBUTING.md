# Contributing Guide

## Adding a New Event Handler

Follow these steps to add monitoring for a new AWS event:

### 1. Identify the Event

Find the CloudTrail event name you want to monitor:
- Check AWS CloudTrail console
- Review AWS service documentation
- Use CloudTrail Insights

Example: `CreateDBCluster` for RDS cluster creation

### 2. Choose or Create Handler File

Organize by AWS service:
- EC2/VPC events → `handlers/ec2_handler.py` or `handlers/vpc_handler.py`
- IAM events → `handlers/iam_handler.py`
- S3 events → `handlers/s3_handler.py`
- New service → Create `handlers/{service}_handler.py`

### 3. Implement Handler Function

```python
from typing import Dict, Any, List
from core.event_types import EventDetail
from utils.logger import setup_logger

logger = setup_logger(__name__)


def handle_new_event(event: Dict[str, Any], context: Any) -> List[EventDetail]:
    """
    Detect security violations in {service} {action}.
    
    Args:
        event: CloudTrail event from EventBridge
        context: Lambda context object
    
    Returns:
        List of EventDetail dictionaries describing violations
    """
    logger.info("Processing {event_name} event")
    
    # Extract event details
    detail = event['detail']
    request_params = detail.get('requestParameters', {})
    response_elements = detail.get('responseElements', {})
    
    # Check for violations
    violations = []
    
    # Example: Check if resource is public
    if request_params.get('publiclyAccessible'):
        violations.append(EventDetail(
            title=f"Public {resource_type} created: {resource_id}",
            source_ip_address=detail.get('sourceIPAddress', ''),
            event_source=detail['eventSource'],
            event_name=detail['eventName'],
            resource_name=resource_id,
            resource_value="Public"
        ))
    
    logger.info(f"Found {len(violations)} violation(s)")
    return violations
```

### 4. Register Handler in main.py

Add to the imports section:
```python
from handlers.your_handler import handle_new_event
```

Register the handler:
```python
register_handler('EventName')(handle_new_event)
```

### 5. Update CloudFormation Template

Add the event to the EventBridge rule in `AWS-Generic-Security-Template.yml`:

```yaml
detail:
  eventName:
    - EventName  # Add your event here
```

### 6. Update handlers/__init__.py

Export your handler:
```python
from handlers.your_handler import handle_new_event

__all__ = [
    # ... existing handlers
    'handle_new_event',
]
```

### 7. Test Your Handler

Create a test event file `test_events/event_name.json`:

```json
{
  "version": "0",
  "id": "test-event-id",
  "detail-type": "AWS API Call via CloudTrail",
  "source": "aws.service",
  "time": "2024-01-01T00:00:00Z",
  "region": "us-east-1",
  "detail": {
    "eventName": "EventName",
    "eventSource": "service.amazonaws.com",
    "sourceIPAddress": "1.2.3.4",
    "userIdentity": {
      "type": "IAMUser",
      "accountId": "123456789012",
      "arn": "arn:aws:iam::123456789012:user/test"
    },
    "requestParameters": {
      // Add test parameters
    },
    "responseElements": {
      // Add test response
    }
  }
}
```

Test locally:
```python
import json
from handlers.your_handler import handle_new_event

with open('test_events/event_name.json') as f:
    event = json.load(f)

result = handle_new_event(event, None)
print(result)
```

### 8. Deploy and Verify

```bash
# Package and deploy layer
./deploy.sh

# Update CloudFormation stack
aws cloudformation update-stack \
  --stack-name aws-security-monitoring \
  --template-body file://AWS-Generic-Security-Template.yml \
  --parameters ParameterKey=LambdaLayerVersion,ParameterValue=NEW_VERSION \
  --capabilities CAPABILITY_NAMED_IAM

# Trigger test event
aws events put-events --entries file://test_events/event_name.json

# Check logs
aws logs tail /aws/lambda/AWS-Generic-Security-us-east-1 --follow
```

## Code Style Guidelines

### Python Style
- Follow PEP 8
- Use type hints for all function signatures
- Add docstrings to all functions
- Keep functions focused and single-purpose
- Maximum line length: 100 characters

### Naming Conventions
- Functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_leading_underscore`

### Error Handling
- Use custom exceptions from `core.exceptions`
- Log errors with context
- Return empty list instead of raising exceptions in handlers
- Let main.py handle top-level exception catching

### Logging
- Use structured logging with context
- Log levels:
  - `DEBUG`: Detailed diagnostic information
  - `INFO`: General informational messages
  - `WARNING`: Warning messages for non-critical issues
  - `ERROR`: Error messages for failures

Example:
```python
logger.info(f"Processing event: {event_name}", extra={
    'event_name': event_name,
    'resource_id': resource_id,
    'region': region
})
```

## Testing Checklist

- [ ] Handler returns `List[EventDetail]`
- [ ] Handler returns empty list when no violations
- [ ] Handler includes descriptive `title` field
- [ ] Handler logs appropriately
- [ ] Handler handles missing fields gracefully
- [ ] Event registered in `main.py`
- [ ] Event added to CloudFormation template
- [ ] Handler exported in `__init__.py`
- [ ] Test event created
- [ ] Local testing passed
- [ ] Deployed and verified in AWS

## Common Patterns

### Checking for Public Access
```python
from core.constants import PUBLIC_IPV4_CIDR, PUBLIC_IPV6_CIDR

def is_public(cidr: str) -> bool:
    return cidr in [PUBLIC_IPV4_CIDR, PUBLIC_IPV6_CIDR]
```

### Extracting Resource IDs
```python
# From response elements
resource_id = response_elements.get('resourceId', 'Unknown')

# From request parameters
resource_id = request_params.get('resourceId', 'Unknown')

# From nested structures
resource_id = (response_elements
               .get('resource', {})
               .get('resourceId', 'Unknown'))
```

### Checking Multiple Conditions
```python
violations = []

for item in items:
    if condition1(item) and condition2(item):
        violations.append(EventDetail(
            title=f"Violation in {item['id']}",
            # ... other fields
        ))

return violations
```

## Questions?

- Review existing handlers for examples
- Check `ARCHITECTURE.md` for design patterns
- Open an issue for clarification
