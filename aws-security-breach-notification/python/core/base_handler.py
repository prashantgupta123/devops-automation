"""Base handler class for AWS security event processing."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from core.event_types import EventDetail
from utils.logger import setup_logger


class BaseHandler(ABC):
    """
    Abstract base class for security event handlers.
    
    Provides common functionality and enforces consistent interface.
    """
    
    def __init__(self):
        self.logger = setup_logger(self.__class__.__name__)
    
    @abstractmethod
    def handle(self, event: Dict[str, Any], context: Any) -> List[EventDetail]:
        """
        Process the security event and return violations.
        
        Args:
            event: CloudTrail event from EventBridge
            context: Lambda context object
        
        Returns:
            List of EventDetail dictionaries describing violations
        """
        pass
    
    def get_event_detail(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Extract the detail section from the event."""
        return event.get('detail', {})
    
    def get_request_parameters(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Extract request parameters from the event."""
        return self.get_event_detail(event).get('requestParameters', {})
    
    def get_response_elements(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Extract response elements from the event."""
        return self.get_event_detail(event).get('responseElements', {})
    
    def get_source_ip(self, event: Dict[str, Any]) -> str:
        """Extract source IP address from the event."""
        return self.get_event_detail(event).get('sourceIPAddress', '')
    
    def get_event_name(self, event: Dict[str, Any]) -> str:
        """Extract event name from the event."""
        return self.get_event_detail(event).get('eventName', '')
    
    def get_event_source(self, event: Dict[str, Any]) -> str:
        """Extract event source from the event."""
        return self.get_event_detail(event).get('eventSource', '')
    
    def get_region(self, event: Dict[str, Any]) -> str:
        """Extract AWS region from the event."""
        return self.get_event_detail(event).get('awsRegion', '')
