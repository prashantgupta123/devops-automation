# Unauthenticated APIs Report

A security automation tool that scans API endpoints to identify unauthenticated access vulnerabilities. This tool tests various HTTP methods and authentication schemes to detect APIs that may be exposing data without proper authentication.

## Overview

This solution automatically tests API endpoints for authentication bypass vulnerabilities by:
- Testing multiple HTTP methods (GET, POST, PUT, DELETE)
- Attempting access without authentication headers
- Testing with invalid authentication tokens
- Generating comprehensive security reports

## Features

- **Multi-Method Testing**: Tests GET, POST, PUT, DELETE methods
- **Authentication Bypass Detection**: Identifies APIs accessible without proper auth
- **Token Validation**: Tests with various authentication schemes (Bearer, Basic)
- **Automated Reporting**: Generates detailed security reports
- **Email Notifications**: Sends alerts for security findings
- **Concurrent Processing**: Multi-threaded scanning for efficiency

## Prerequisites

- Python 3.13+
- Required Python packages (see requirements.txt)
- Network access to target APIs
- Email configuration for notifications

## Installation

```bash
# Navigate to the solution directory
cd unauthenticated-apis-report

# Install dependencies
pip install -r requirements.txt
```

## Configuration

### API List Configuration
Create `unauthenticated-api.json` with your API endpoints:

```json
{
  "data": [
    "https://api.example.com/v1/users",
    "https://api.example.com/v1/orders",
    "https://api.example.com/v1/admin"
  ]
}
```

### Notification Setup
Configure email notifications in the `Notification` module for security alerts.

## Usage

### Basic Scan
```bash
python unauthenticated-api.py
```

### Key Functions

- `get_api_list()`: Loads API endpoints from configuration
- `check_authentication(api_url)`: Tests authentication for specific endpoint
- `get_api_authentication()`: Performs individual authentication tests
- `generate_password()`: Creates random tokens for testing

## Security Testing Methods

### 1. No Authentication Headers
Tests if APIs respond successfully without any authentication.

### 2. Invalid Token Testing
Tests with randomly generated tokens to identify weak validation.

### 3. Authentication Scheme Testing
- Bearer token validation
- Basic authentication testing
- Custom authorization headers

### 4. HTTP Method Testing
Tests all common HTTP methods for each endpoint.

## Report Output

The tool generates detailed reports including:
- Request/response details
- Authentication status
- Vulnerability findings
- Remediation recommendations

## Security Considerations

- **Ethical Use**: Only scan APIs you own or have permission to test
- **Rate Limiting**: Implement delays to avoid overwhelming target systems
- **Credential Security**: Never use real credentials in testing
- **Network Security**: Run from secure, authorized networks only

## Integration

### CI/CD Pipeline
Integrate into security scanning workflows:
```bash
# Add to pipeline
python unauthenticated-api.py --output-format json
```

### Monitoring
Set up regular scans to monitor for new vulnerabilities.

## Troubleshooting

### Common Issues
- **Connection Timeouts**: Increase timeout values for slow APIs
- **Rate Limiting**: Add delays between requests
- **SSL Errors**: Configure proper certificate validation

### Debug Mode
Enable verbose logging for detailed troubleshooting.

## Contributing

1. Add new authentication schemes to test
2. Enhance reporting capabilities
3. Improve error handling
4. Add support for additional HTTP methods

## License

MIT License - Use responsibly and ethically.

## Security Notice

This tool is designed for authorized security testing only. Ensure you have proper permission before scanning any APIs. Unauthorized testing may violate terms of service or applicable laws.