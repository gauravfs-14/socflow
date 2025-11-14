"""Configuration management with hierarchical settings."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseModel):
    """Database configuration."""
    
    type: str = Field(default="sqlite", description="Database type: sqlite, postgresql, mysql")
    path: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    separate_databases: bool = Field(default=False, description="Use separate databases for each platform")
    
    @validator('type')
    def validate_type(cls, v):
        allowed_types = ['sqlite', 'postgresql', 'mysql']
        if v not in allowed_types:
            raise ValueError(f"Database type must be one of {allowed_types}")
        return v


class RedditConfig(BaseModel):
    """Reddit collector configuration."""
    
    enabled: bool = Field(default=True, description="Enable Reddit collector")
    subreddits: List[str] = Field(default=["all"], description="List of subreddits to collect from")
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    user_agent: str = Field(default="SocFlow/1.0", description="User agent for Reddit API")
    max_posts_per_subreddit: int = Field(default=1000, description="Maximum posts to collect per subreddit")
    sort_by: str = Field(default="hot", description="Sort posts by: hot, new, top, rising")
    time_filter: str = Field(default="day", description="Time filter for top posts: hour, day, week, month, year, all")
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        allowed_sorts = ['hot', 'new', 'top', 'rising']
        if v not in allowed_sorts:
            raise ValueError(f"Sort by must be one of {allowed_sorts}")
        return v
    
    @validator('time_filter')
    def validate_time_filter(cls, v):
        allowed_filters = ['hour', 'day', 'week', 'month', 'year', 'all']
        if v not in allowed_filters:
            raise ValueError(f"Time filter must be one of {allowed_filters}")
        return v


class BlueskyConfig(BaseModel):
    """Bluesky collector configuration."""
    
    enabled: bool = Field(default=True, description="Enable Bluesky collector")
    handle: Optional[str] = None
    password: Optional[str] = None
    max_posts: int = Field(default=1000, description="Maximum posts to collect")
    keywords: List[str] = Field(default=[], description="Keywords to search for")


class MastodonConfig(BaseModel):
    """Mastodon collector configuration."""
    
    enabled: bool = Field(default=True, description="Enable Mastodon collector")
    instances: List[str] = Field(default=["https://mastodon.social"], description="Mastodon instances to collect from")
    access_token: Optional[str] = None
    max_posts_per_instance: int = Field(default=1000, description="Maximum posts to collect per instance")
    hashtags: List[str] = Field(default=[], description="Hashtags to search for")


class CollectorsConfig(BaseModel):
    """Collectors configuration."""
    
    reddit: RedditConfig = Field(default_factory=RedditConfig)
    bluesky: BlueskyConfig = Field(default_factory=BlueskyConfig)
    mastodon: MastodonConfig = Field(default_factory=MastodonConfig)


class AppConfig(BaseModel):
    """Application configuration."""
    
    name: str = Field(default="SocFlow", description="Application name")
    output_dir: str = Field(default="data", description="Output directory for data")
    log_level: str = Field(default="INFO", description="Logging level")
    debug: bool = Field(default=False, description="Enable debug mode")
    
    @validator('log_level')
    def validate_log_level(cls, v):
        allowed_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed_levels:
            raise ValueError(f"Log level must be one of {allowed_levels}")
        return v.upper()


class Settings(BaseSettings):
    """Main settings class with hierarchical configuration."""
    
    app: AppConfig = Field(default_factory=AppConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    collectors: CollectorsConfig = Field(default_factory=CollectorsConfig)
    
    class Config:
        env_prefix = "SOCFLOW_"
        case_sensitive = False


def load_settings(config_path: Optional[Union[str, Path]] = None) -> Settings:
    """Load settings from YAML file and environment variables.
    
    Args:
        config_path: Path to YAML configuration file. If None, looks for:
            - Current directory: ./socflow.yml or ./.socflow/config.yml
            - User config: ~/.socflow/config.yml
            - Dev config: ./config/settings.yml (for development)
            - Default config: ./config/settings.default.yml (for development)
    
    Returns:
        Settings object with loaded configuration
    """
    # Load environment variables from .env file
    load_dotenv(override=True)
    
    if config_path is None:
        # Get current working directory
        cwd = Path.cwd()
        
        # Try to find config file in order of preference
        possible_paths = [
            cwd / "socflow.yml",  # Current directory config
            cwd / ".socflow" / "config.yml",  # Current directory hidden config
            Path.home() / ".socflow" / "config.yml",  # User config
            Path("config/settings.yml"),  # Dev config (relative to project root)
            Path("config/settings.default.yml"),  # Default config (relative to project root)
        ]
        
        for path in possible_paths:
            if path.exists():
                config_path = path
                break
        else:
            # If no config file found, return default settings
            return Settings()
    
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    # Load YAML configuration
    with open(config_path, 'r') as f:
        yaml_config = yaml.safe_load(f)
    
    # Create settings from YAML and environment variables
    settings = Settings(**yaml_config)
    
    return settings


def save_user_config(settings: Settings, user_config_path: Optional[Path] = None) -> None:
    """Save settings to user configuration file.
    
    Args:
        settings: Settings object to save
        user_config_path: Path to save user config. If None, uses current directory socflow.yml
    """
    if user_config_path is None:
        # Default to current directory
        cwd = Path.cwd()
        user_config_path = cwd / "socflow.yml"
    
    # Create directory if it doesn't exist
    user_config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert settings to dict and save as YAML
    config_dict = settings.dict()
    
    with open(user_config_path, 'w') as f:
        yaml.dump(config_dict, f, default_flow_style=False, indent=2)
