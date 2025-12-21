# Kong Service Routes Automation

Automated Kong API Gateway service and route management tool that creates and configures Kong services, routes, plugins, and consumers based on JSON configuration.

## Overview

This automation tool streamlines Kong API Gateway configuration by:
- Creating and managing Kong services
- Setting up routes with custom configurations
- Configuring plugins for services and routes
- Managing consumers and their credentials
- Validating existing configurations to prevent duplicates

## Features

- **Service Management**: Automated creation and validation of Kong services
- **Route Configuration**: Dynamic route creation with host and path matching
- **Plugin Support**: Automated plugin configuration for services and routes
- **Consumer Management**: Consumer creation with JWT credential support
- **Duplicate Prevention**: Validates existing resources before creation
- **Comprehensive Logging**: Detailed logging with file and console output
- **JSON Configuration**: Flexible configuration through input.json file

## Prerequisites

- Python 3.13+
- Kong API Gateway instance
- Network access to Kong Admin API
- Required Python packages (see requirements.txt)

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd kong-service-routes

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Create an `input.json` file with your Kong configuration:

```json
{
  "admin": {
    "kong": {
      "host": "http://localhost:8001"
    }
  },
  "services": {
    "example-service": {
      "service": {
        "name": "example-service",
        "url": "http://backend.example.com",
        "id": ""
      },
      "plugins": {
        "rate-limiting": {
          "plugin": {
            "name": "rate-limiting",
            "config": {
              "minute": 100
            }
          }
        }
      }
    }
  },
  "projects": {
    "example-project": {
      "tools": {
        "service": "example-service",
        "routes": {
          "api-route": {
            "route": {
              "name": "api-route",
              "hosts": ["api.example.com"],
              "paths": ["/api"]
            },
            "plugins": {
              "jwt": {
                "plugin": {
                  "name": "jwt"
                }
              }
            },
            "consumers": {
              "api-consumer": {
                "consumer": {
                  "username": "api-user"
                },
                "credentials": {
                  "jwt-credential": {
                    "credential": {
                      "key": "api-key"
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

## Usage

### Basic Execution

```bash
python function.py
```

### Configuration Structure

#### Admin Configuration
- **host**: Kong Admin API endpoint

#### Services Configuration
- **name**: Service identifier
- **url**: Backend service URL
- **plugins**: Service-level plugins configuration

#### Projects Configuration
- **service**: Reference to service name
- **routes**: Route configurations with hosts and paths
- **plugins**: Route-level plugins
- **consumers**: Consumer and credential management

## Supported Kong Resources

### Services
- Service creation and validation
- URL and protocol configuration
- Service-level plugin attachment

### Routes
- Host-based routing
- Path-based routing
- Route naming with project prefixes
- Route validation to prevent duplicates

### Plugins
- Rate limiting
- JWT authentication
- CORS configuration
- Custom plugin configurations

### Consumers
- Consumer creation
- JWT credential management
- Multiple credential types support

## Logging

The tool provides comprehensive logging:

- **File Logging**: `kong_service_routes.log`
- **Console Output**: Real-time execution feedback
- **Log Levels**: INFO, DEBUG, WARNING, ERROR

### Log Configuration

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('kong_service_routes.log'),
        logging.StreamHandler()
    ]
)
```

## Error Handling

The tool includes robust error handling for:
- Kong API connection failures
- Invalid configuration data
- Resource creation conflicts
- Authentication errors

## Security Considerations

- **Credentials**: Never commit actual credentials to version control
- **API Access**: Ensure Kong Admin API is properly secured
- **Network Security**: Use HTTPS for production deployments
- **Access Control**: Implement proper IAM for Kong Admin API access

## Troubleshooting

### Common Issues

1. **Connection Refused**
   ```
   Failed to retrieve services: Connection refused
   ```
   - Verify Kong Admin API is running
   - Check host configuration in input.json

2. **Authentication Errors**
   ```
   Failed to create service: 401 Unauthorized
   ```
   - Verify Kong Admin API authentication
   - Check network connectivity

3. **Configuration Errors**
   ```
   Service data not found
   ```
   - Validate input.json structure
   - Ensure all required fields are present

### Debug Mode

Enable debug logging for detailed troubleshooting:

```python
logging.getLogger().setLevel(logging.DEBUG)
```

## Development

### Project Structure
```
kong-service-routes/
├── function.py           # Main automation script
├── input.json           # Configuration file (create from example)
├── requirements.txt     # Python dependencies
├── kong_service_routes.log  # Generated log file
└── README.md           # This documentation
```

### Adding New Features

1. **New Plugin Support**: Extend plugin configuration in input.json
2. **Additional Resources**: Add new Kong resource types
3. **Enhanced Validation**: Improve duplicate detection logic

## Dependencies

```txt
requests>=2.25.0
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Add comprehensive tests
4. Update documentation
5. Submit pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Check the troubleshooting section
- Review log files for detailed error information
- Ensure Kong API Gateway is properly configured

---

**Note**: Always test configurations in non-production environments before deploying to production Kong instances.