"""Base database manager interface."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from ..models.base import BasePost


class DatabaseType(Enum):
    """Supported database types."""
    
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"


class DatabaseManager(ABC):
    """Abstract base class for database managers."""
    
    def __init__(self, connection_string: str, separate_databases: bool = False):
        """Initialize database manager.
        
        Args:
            connection_string: Database connection string
            separate_databases: Whether to use separate databases for each platform
        """
        self.connection_string = connection_string
        self.separate_databases = separate_databases
        self.engine: Optional[Engine] = None
        self.session_factory: Optional[sessionmaker] = None
        self._setup_connection()
    
    @abstractmethod
    def _setup_connection(self) -> None:
        """Setup database connection."""
        pass
    
    @abstractmethod
    def create_tables(self, platforms: List[str]) -> None:
        """Create necessary tables.
        
        Args:
            platforms: List of platform names to create tables for
        """
        pass
    
    @abstractmethod
    def insert_post(self, post: BasePost) -> None:
        """Insert a single post.
        
        Args:
            post: Post to insert
        """
        pass
    
    @abstractmethod
    def insert_posts(self, posts: List[BasePost]) -> None:
        """Insert multiple posts.
        
        Args:
            posts: List of posts to insert
        """
        pass
    
    @abstractmethod
    def get_posts(
        self, 
        platform: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get posts from database.
        
        Args:
            platform: Filter by platform
            limit: Maximum number of posts to return
            offset: Number of posts to skip
            
        Returns:
            List of post dictionaries
        """
        pass
    
    @abstractmethod
    def get_post_count(self, platform: Optional[str] = None) -> int:
        """Get total number of posts.
        
        Args:
            platform: Filter by platform
            
        Returns:
            Number of posts
        """
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close database connection."""
        pass
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
