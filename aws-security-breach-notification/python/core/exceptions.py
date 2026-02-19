"""Custom exceptions for AWS security monitoring."""


class SecurityMonitoringError(Exception):
    """Base exception for security monitoring errors."""
    pass


class ConfigurationError(SecurityMonitoringError):
    """Raised when configuration is invalid or missing."""
    pass


class HandlerError(SecurityMonitoringError):
    """Raised when a handler encounters an error."""
    pass


class NotificationError(SecurityMonitoringError):
    """Raised when notification sending fails."""
    pass
