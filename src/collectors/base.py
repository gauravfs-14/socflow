"""Base collector interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..models.base import BasePost


class BaseCollector(ABC):
    """Abstract base class for data collectors."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize collector with configuration.
        
        Args:
            config: Collector-specific configuration
        """
        self.config = config
        self.enabled = config.get("enabled", True)
    
    @abstractmethod
    def collect(self, **kwargs) -> List[BasePost]:
        """Collect data from the platform.
        
        Args:
            **kwargs: Platform-specific collection parameters
            
        Returns:
            List of collected posts
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate collector configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """Get platform name.
        
        Returns:
            Platform name
        """
        pass
    
    def is_enabled(self) -> bool:
        """Check if collector is enabled.
        
        Returns:
            True if enabled, False otherwise
        """
        return self.enabled
    
    def get_config(self) -> Dict[str, Any]:
        """Get collector configuration.
        
        Returns:
            Configuration dictionary
        """
        return self.config
