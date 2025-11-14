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
    from pathlib import Path
    
    db_type = DatabaseType(config.type)
    
    if db_type == DatabaseType.SQLITE:
        if config.path:
            # If path is relative, make it relative to current working directory
            db_path = Path(config.path)
            if not db_path.is_absolute():
                db_path = Path.cwd() / db_path
            connection_string = f"sqlite:///{db_path}"
        else:
            # Default to current working directory
            cwd = Path.cwd()
            db_path = cwd / "data" / "socflow.db"
            connection_string = f"sqlite:///{db_path}"
        
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
