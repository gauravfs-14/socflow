"""Pytest configuration and shared fixtures."""

import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest
import yaml

from src.config.settings import Settings
from src.database.factory import create_database_manager
from src.models.base import BasePost, Metrics
from datetime import datetime


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_config_file(temp_dir: Path) -> Path:
    """Create a temporary config file."""
    config_path = temp_dir / "socflow.yml"
    config_data = {
        'app': {
            'name': 'SocFlow',
            'output_dir': 'data',
            'log_level': 'DEBUG',
            'debug': True
        },
        'database': {
            'type': 'sqlite',
            'path': str(temp_dir / 'test.db'),
            'separate_databases': False
        },
        'collectors': {
            'reddit': {
                'enabled': False,  # Disabled for tests unless needed
                'subreddits': ['test'],
                'user_agent': 'SocFlow-Test/1.0',
                'max_posts_per_subreddit': 10,
                'sort_by': 'hot',
                'time_filter': 'day'
            },
            'bluesky': {
                'enabled': False,
                'max_posts': 10,
                'keywords': []
            },
            'mastodon': {
                'enabled': False,
                'instances': ['https://mastodon.social'],
                'max_posts_per_instance': 10,
                'hashtags': []
            }
        }
    }
    
    with open(config_path, 'w') as f:
        yaml.dump(config_data, f)
    
    return config_path


@pytest.fixture
def test_settings(temp_config_file: Path) -> Settings:
    """Create test settings from temp config."""
    return Settings(
        app={
            'name': 'SocFlow-Test',
            'output_dir': 'data',
            'log_level': 'DEBUG',
            'debug': True
        },
        database={
            'type': 'sqlite',
            'path': str(temp_config_file.parent / 'test.db'),
            'separate_databases': False
        },
        collectors={
            'reddit': {
                'enabled': False,
                'subreddits': ['test'],
                'user_agent': 'SocFlow-Test/1.0',
                'max_posts_per_subreddit': 10,
                'sort_by': 'hot',
                'time_filter': 'day'
            },
            'bluesky': {
                'enabled': False,
                'max_posts': 10,
                'keywords': []
            },
            'mastodon': {
                'enabled': False,
                'instances': ['https://mastodon.social'],
                'max_posts_per_instance': 10,
                'hashtags': []
            }
        }
    )


@pytest.fixture
def test_db_manager(temp_dir: Path) -> Generator:
    """Create a test database manager."""
    db_path = temp_dir / "test.db"
    connection_string = f"sqlite:///{db_path}"
    
    from src.database.sqlite import SQLiteManager
    manager = SQLiteManager(connection_string, separate_databases=False)
    
    yield manager
    
    manager.close()
    # Clean up
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def sample_post() -> BasePost:
    """Create a sample post for testing."""
    return BasePost(
        platform="test",
        object_id="test_123",
        author_handle="test_user",
        text="This is a test post",
        created_at=datetime.now(),
        tags=[],
        metrics=Metrics(likes=10, comments=5),
        url="https://example.com/post/123",
        is_comment=False
    )


@pytest.fixture
def sample_posts() -> list[BasePost]:
    """Create multiple sample posts for testing."""
    posts = []
    for i in range(5):
        post = BasePost(
            platform="test",
            object_id=f"test_{i}",
            author_handle=f"user_{i}",
            text=f"Test post {i}",
            created_at=datetime.now(),
            tags=[],
            metrics=Metrics(likes=i*10, comments=i*5),
            url=f"https://example.com/post/{i}",
            is_comment=False
        )
        posts.append(post)
    return posts


@pytest.fixture
def mock_collector_config():
    """Mock collector configuration."""
    return {
        'enabled': True,
        'subreddits': ['test'],
        'max_posts': 10
    }

