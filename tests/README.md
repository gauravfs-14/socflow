# SocFlow Test Suite

Comprehensive test suite for SocFlow covering all major components and features.

## Test Structure

```
tests/
├── conftest.py              # Pytest fixtures and configuration
├── test_database.py         # Database operations and thread safety
├── test_config.py           # Configuration management
├── test_models.py           # Data models (BasePost, Metrics)
├── test_collectors.py       # Data collectors (mocked)
├── test_app.py              # Main application and CLI
├── test_concurrency.py      # Concurrency and thread safety (Python 3.14+)
└── test_integration.py      # End-to-end integration tests
```

## Running Tests

### Run All Tests

```bash
# Using pytest directly
pytest

# Using uv
uv run pytest

# With coverage
uv run pytest --cov=src --cov-report=html
```

### Run Specific Test Files

```bash
# Test database operations
pytest tests/test_database.py

# Test configuration
pytest tests/test_config.py

# Test concurrency
pytest tests/test_concurrency.py
```

### Run Specific Test Classes or Functions

```bash
# Run a specific test class
pytest tests/test_database.py::TestSQLiteManager

# Run a specific test
pytest tests/test_database.py::TestSQLiteManager::test_insert_single_post
```

### Run Tests by Marker

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

## Test Coverage

The test suite covers:

- ✅ **Database Operations**: CRUD operations, deduplication, thread safety
- ✅ **Configuration Management**: Loading, saving, validation, priority
- ✅ **Data Models**: BasePost, Metrics, serialization
- ✅ **Collectors**: Initialization, enabled/disabled states (mocked)
- ✅ **Application**: Initialization, stats, export, CLI commands
- ✅ **Concurrency**: Thread-safe operations, concurrent inserts/reads
- ✅ **Integration**: End-to-end workflows, error handling

## Thread Safety Tests

The test suite includes comprehensive thread safety tests for Python 3.14+:

- Concurrent database inserts
- Concurrent reads
- Concurrent read/write operations
- Connection pooling
- Performance benchmarks

## Fixtures

Common fixtures available in `conftest.py`:

- `temp_dir`: Temporary directory for test files
- `temp_config_file`: Temporary configuration file
- `test_settings`: Test settings object
- `test_db_manager`: Test database manager
- `sample_post`: Sample BasePost instance
- `sample_posts`: Multiple sample posts
- `mock_collector_config`: Mock collector configuration

## Writing New Tests

When adding new tests:

1. Follow the naming convention: `test_*.py` for files, `test_*` for functions
2. Use fixtures from `conftest.py` when possible
3. Mark slow tests with `@pytest.mark.slow`
4. Mark integration tests with `@pytest.mark.integration`
5. Use `unittest.mock` for mocking external dependencies
6. Test both success and error cases

Example:

```python
import pytest
from src.models.base import BasePost

def test_my_feature(sample_post):
    """Test my new feature."""
    # Your test code here
    assert sample_post.platform == "test"
```

## Continuous Integration

Tests are designed to run in CI/CD environments:

- All tests use temporary directories (no file system pollution)
- Tests are isolated and can run in parallel
- No external dependencies required (collectors are mocked)
- Thread safety tests verify Python 3.14+ concurrency features
