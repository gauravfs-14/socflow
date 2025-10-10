"""Database manager factory."""

from typing import Optional

from ..config.settings import DatabaseConfig
from .base import DatabaseManager, DatabaseType
from .sqlite import SQLiteManager


def create_database_manager(config: DatabaseConfig) -> DatabaseManager:
    """Create database manager based on configuration.
    
    Args:
        config: Database configuration
        
    Returns:
        Database manager instance
        
    Raises:
        ValueError: If database type is not supported
    """
    db_type = DatabaseType(config.type)
    
    if db_type == DatabaseType.SQLITE:
        if config.path:
            connection_string = f"sqlite:///{config.path}"
        else:
            connection_string = "sqlite:///data/socflow.db"
        
        return SQLiteManager(
            connection_string=connection_string,
            separate_databases=config.separate_databases
        )
    
    elif db_type == DatabaseType.POSTGRESQL:
        # TODO: Implement PostgreSQL manager
        raise NotImplementedError("PostgreSQL support not yet implemented")
    
    elif db_type == DatabaseType.MYSQL:
        # TODO: Implement MySQL manager
        raise NotImplementedError("MySQL support not yet implemented")
    
    else:
        raise ValueError(f"Unsupported database type: {config.type}")
