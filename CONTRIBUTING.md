# Contributing to SocFlow

Thank you for your interest in contributing to SocFlow! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- UV package manager (recommended) or pip

### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/gauravfs-14/socflow.git
cd socflow

# Create a virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv sync

# Install development dependencies
make install

# Setup pre-commit hooks
pre-commit install
```

## 🛠️ Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Write clean, readable code
- Add appropriate comments and docstrings
- Follow the existing code style
- Add tests for new functionality

### 3. Test Your Changes

```bash
# Run all tests
make test

# Run specific tests
python -m pytest tests/test_your_feature.py

# Run linting
make lint

# Format code
make format
```

### 4. Commit Your Changes

```bash
# Add your changes
git add .

# Commit with a descriptive message
git commit -m "feat: add new feature for X"

# Push to your fork
git push origin feature/your-feature-name
```

### 5. Create a Pull Request

- Go to the GitHub repository
- Click "New Pull Request"
- Select your feature branch
- Fill out the PR template
- Submit the PR

## 📝 Code Style Guidelines

### Python Code Style

We follow [PEP 8](https://pep8.org/) with some modifications:

- **Line Length**: 88 characters (Black default)
- **Imports**: Use absolute imports, group by standard library, third-party, local
- **Docstrings**: Use Google style docstrings
- **Type Hints**: Use type hints for all function parameters and return values

### Example Code Style

```python
from typing import List, Optional, Dict, Any
from datetime import datetime

from .base import BaseCollector
from ..models.reddit import RedditPost


class RedditCollector(BaseCollector):
    """Reddit data collector implementation.
    
    This collector handles data collection from Reddit using the PRAW library.
    It supports both subreddit feeds and keyword-based search.
    
    Args:
        config: Configuration dictionary for the collector
        credentials: API credentials for Reddit
    """
    
    def __init__(self, config: Dict[str, Any], credentials: Dict[str, str]):
        """Initialize the Reddit collector.
        
        Args:
            config: Configuration dictionary
            credentials: API credentials
        """
        super().__init__(config, credentials)
        self.reddit = self._setup_reddit_client()
    
    def collect_continuous(self, subreddits: Optional[List[str]] = None) -> List[RedditPost]:
        """Collect posts continuously from Reddit.
        
        Args:
            subreddits: List of subreddits to collect from
            
        Returns:
            List of collected Reddit posts
            
        Raises:
            ValueError: If invalid subreddit names are provided
        """
        # Implementation here
        pass
```

## 🧪 Testing Guidelines

### Test Structure

```
tests/
├── test_collectors/          # Collector tests
│   ├── test_reddit.py
│   ├── test_bluesky.py
│   └── test_mastodon.py
├── test_database/            # Database tests
│   ├── test_sqlite.py
│   └── test_models.py
├── test_app/                 # Application tests
│   ├── test_cli.py
│   └── test_tui.py
├── fixtures/                 # Test fixtures
│   ├── reddit_posts.json
│   └── bluesky_posts.json
└── conftest.py              # Pytest configuration
```

### Writing Tests

```python
import pytest
from unittest.mock import Mock, patch
from src.collectors.reddit import RedditCollector
from src.models.reddit import RedditPost


class TestRedditCollector:
    """Test cases for RedditCollector."""
    
    @pytest.fixture
    def collector(self):
        """Create a RedditCollector instance for testing."""
        config = {"subreddits": ["all"], "max_posts": 10}
        credentials = {"client_id": "test", "client_secret": "test"}
        return RedditCollector(config, credentials)
    
    def test_collect_continuous(self, collector):
        """Test continuous collection from Reddit."""
        with patch.object(collector, '_collect_from_subreddit') as mock_collect:
            mock_collect.return_value = [Mock(spec=RedditPost)]
            posts = collector.collect_continuous()
            assert len(posts) > 0
            mock_collect.assert_called_once()
    
    def test_invalid_subreddit(self, collector):
        """Test handling of invalid subreddit names."""
        with pytest.raises(ValueError):
            collector.collect_continuous(subreddits=["invalid_subreddit_12345"])
```

### Test Coverage

We aim for high test coverage:

- **Minimum**: 80% overall coverage
- **Target**: 90% overall coverage
- **Critical paths**: 100% coverage

## 📚 Documentation Guidelines

### Docstring Format

Use Google style docstrings:

```python
def collect_posts(self, subreddits: List[str], max_posts: int = 100) -> List[RedditPost]:
    """Collect posts from specified subreddits.
    
    This method fetches posts from the given subreddits using the Reddit API.
    It handles rate limiting and error recovery automatically.
    
    Args:
        subreddits: List of subreddit names to collect from
        max_posts: Maximum number of posts to collect per subreddit
        
    Returns:
        List of RedditPost objects containing the collected data
        
    Raises:
        ValueError: If subreddits list is empty
        APIError: If Reddit API returns an error
        
    Example:
        >>> collector = RedditCollector(config, credentials)
        >>> posts = collector.collect_posts(['all', 'python'], max_posts=50)
        >>> len(posts)
        100
    """
```

### README Updates

When adding new features:

1. Update the Features section
2. Add usage examples
3. Update the Makefile commands
4. Add configuration examples

## 🏗️ Architecture Guidelines

### Adding New Collectors

1. **Create the collector class**:

   ```python
   from .base import BaseCollector
   
   class NewPlatformCollector(BaseCollector):
       """Collector for New Platform."""
       
       def collect_continuous(self, **kwargs):
           """Implement continuous collection."""
           pass
   ```

2. **Create data models**:

   ```python
   from ..models.base import BasePost, BaseMetrics
   
   class NewPlatformMetrics(BaseMetrics):
       """Metrics specific to New Platform."""
       pass
   
   class NewPlatformPost(BasePost):
       """Post model for New Platform."""
       pass
   ```

3. **Update the main application**:

   ```python
   # In src/app.py
   from .collectors.new_platform import NewPlatformCollector
   
   def _setup_collectors(self):
       # Add new collector
       pass
   ```

### Adding New Database Types

1. **Create database manager**:

   ```python
   from .base import DatabaseManager
   
   class PostgreSQLManager(DatabaseManager):
       """PostgreSQL database manager."""
       
       def create_tables(self, platforms: List[str]):
           """Create database tables."""
           pass
   ```

2. **Update factory**:

   ```python
   # In src/database/factory.py
   def create_database_manager(db_type: str, **kwargs):
       if db_type == "postgresql":
           return PostgreSQLManager(**kwargs)
   ```

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Environment information**:
   - Python version
   - Operating system
   - SocFlow version

2. **Steps to reproduce**:
   - Clear, numbered steps
   - Expected vs actual behavior

3. **Error messages**:
   - Full traceback
   - Log files if available

4. **Additional context**:
   - Configuration files
   - Sample data if relevant

## 💡 Feature Requests

When requesting features:

1. **Describe the problem**:
   - What use case does this solve?
   - Why is this important?

2. **Propose a solution**:
   - How should this work?
   - Any implementation ideas?

3. **Consider alternatives**:
   - Are there existing solutions?
   - What are the trade-offs?

## 🔄 Pull Request Process

### PR Requirements

- [ ] Code follows style guidelines
- [ ] Tests pass and coverage is maintained
- [ ] Documentation is updated
- [ ] Commit messages are descriptive
- [ ] PR description is clear and complete

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or clearly marked)
```

## 📞 Getting Help

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For questions and general discussion

## 🎉 Recognition

Contributors will be recognized in:

- **README.md**: Contributors section
- **CHANGELOG.md**: Release notes
- **GitHub**: Contributor statistics

Thank you for contributing to SocFlow! 🚀
