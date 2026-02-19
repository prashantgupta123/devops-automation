"""Enumerations for AWS security monitoring."""

from enum import Enum


class EventType(str, Enum):
    """Event notification types."""
    EVENT = "event"
    INFO = "info"
    ERROR = "error"
