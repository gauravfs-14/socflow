# SocFlow Makefile
# Easy commands for development and deployment

.PHONY: help install clean run collect stats export config setup-env setup-config test test-cov test-fast

# Default target
help:
	@echo "SocFlow - Social Media Data Collection Framework"
	@echo ""
	@echo "Available commands:"
	@echo "  setup          - Complete project setup (install, config, env)"
	@echo "  install        - Install dependencies"
	@echo "  clean          - Clean up build artifacts and cache"
	@echo "  run            - Run the application"
	@echo ""
	@echo "Data Collection:"
	@echo "  collect-reddit - Collect data from Reddit"
	@echo "  collect-bluesky- Collect data from Bluesky"
	@echo "  collect-mastodon- Collect data from Mastodon"
	@echo "  collect-all    - Collect data from all platforms"
	@echo ""
	@echo "Continuous Collection:"
	@echo "  collect-tui     - Start TUI for continuous collection (recommended)"
	@echo ""
	@echo "Data Management:"
	@echo "  stats          - Show collection statistics"
	@echo "  export-json    - Export data as JSON"
	@echo "  export-csv     - Export data as CSV"
	@echo "  export-parquet - Export data as Parquet"
	@echo ""
	@echo "Configuration:"
	@echo "  config         - Show current configuration"
	@echo "  setup-env       - Setup environment file"
	@echo "  setup-config    - Setup configuration files"
	@echo "  setup-credentials - Show how to configure API credentials"
	@echo "  setup-db        - Create database tables"
	@echo ""
	@echo "Testing:"
	@echo "  test           - Run all tests"
	@echo "  test-cov       - Run tests with coverage report"
	@echo "  test-fast      - Run fast tests (skip slow tests)"
	@echo "  test-database  - Run database tests only"
	@echo "  test-concurrency - Run concurrency tests only"
	@echo "  test-integration - Run integration tests only"

# Project setup
setup: install setup-env setup-config
	@echo "✅ SocFlow setup complete!"
	@echo "Next steps:"
	@echo "1. Edit .env with your API credentials"
	@echo "2. Run 'make collect-all' to start collecting data"

# Installation
install:
	@echo "📦 Installing SocFlow dependencies..."
	uv sync
	@echo "✅ Dependencies installed"

# Environment setup
setup-env:
	@echo "🔧 Setting up environment file..."
	@if [ ! -f .env ]; then \
		echo "# SocFlow Environment Variables" > .env; \
		echo "# Copy this file to .env and fill in your API credentials" >> .env; \
		echo "" >> .env; \
		echo "# Reddit API Credentials" >> .env; \
		echo "# Get these from https://www.reddit.com/prefs/apps" >> .env; \
		echo "REDDIT_CLIENT_ID=your_reddit_client_id" >> .env; \
		echo "REDDIT_CLIENT_SECRET=your_reddit_client_secret" >> .env; \
		echo "" >> .env; \
		echo "# Bluesky Credentials" >> .env; \
		echo "# Get these from your Bluesky account" >> .env; \
		echo "BLUESKY_HANDLE=your_handle.bsky.app" >> .env; \
		echo "BLUESKY_PASSWORD=your_bluesky_password" >> .env; \
		echo "" >> .env; \
		echo "# Mastodon Credentials" >> .env; \
		echo "# Get these from your Mastodon instance" >> .env; \
		echo "MASTODON_ACCESS_TOKEN=your_mastodon_access_token" >> .env; \
		echo "✅ Environment file created at .env"; \
	else \
		echo "✅ Environment file already exists"; \
	fi

setup-config:
	@echo "🔧 Setting up configuration files..."
	@if [ ! -f config/settings.yml ]; then \
		cp config/settings.default.yml config/settings.yml; \
		echo "✅ Configuration file created at config/settings.yml"; \
	else \
		echo "✅ Configuration file already exists"; \
	fi

# Development
clean:
	@echo "🧹 Cleaning up..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "✅ Cleanup complete"

# Application commands
run:
	@echo "🚀 Running SocFlow..."
	uv run python -m src.main --help

# Data collection commands
collect-reddit:
	@echo "📊 Collecting data from Reddit..."
	uv run python -m src.main collect --platforms reddit --subreddits all --subreddits MachineLearning
	@echo "✅ Reddit collection complete"

collect-bluesky:
	@echo "📊 Collecting data from Bluesky..."
	uv run python -m src.main collect --platforms bluesky --keywords AI --keywords machinelearning
	@echo "✅ Bluesky collection complete"

collect-mastodon:
	@echo "📊 Collecting data from Mastodon..."
	uv run python -m src.main collect --platforms mastodon --hashtags AI --hashtags tech --instances https://mastodon.social
	@echo "✅ Mastodon collection complete"

collect-all:
	@echo "📊 Collecting data from all platforms..."
	uv run python -m src.main collect --platforms reddit --platforms bluesky --platforms mastodon
	@echo "✅ All platforms collection complete"

# Continuous collection commands

# Database setup command
setup-db:
	@echo "🗄️  Setting up database..."
	uv run python -c "from src.app import SocFlowApp; app = SocFlowApp(); platforms = list(app.collectors.keys()); app.db_manager.create_tables(platforms); print('✅ Database created successfully')"

# TUI collection command
collect-tui:
	@echo "🖥️  Starting SocFlow TUI for data collection..."
	@echo "Press Ctrl+C to stop collection"
	uv run python -m src.tui

# TRUE PARALLEL collection using separate processes
collect-parallel:
	@echo "🚀 Starting TRUE PARALLEL collection using separate processes..."
	@echo "This will start 3 separate processes for maximum parallelism"
	@echo "Press Ctrl+C to stop all processes"
	@trap 'pkill -f "uv run python -m src.main collect"; exit' INT; \
	uv run python -m src.main collect --platforms reddit & \
	uv run python -m src.main collect --platforms bluesky & \
	uv run python -m src.main collect --platforms mastodon & \
	wait


# Data management
stats:
	@echo "📈 Showing collection statistics..."
	uv run python -m src.main stats

export-json:
	@echo "📤 Exporting data as JSON..."
	uv run python -m src.main export --output data/export.json
	@echo "✅ JSON export complete"

export-csv:
	@echo "📤 Exporting data as CSV..."
	uv run python -m src.main export --output data/export.csv
	@echo "✅ CSV export complete"

export-parquet:
	@echo "📤 Exporting data as Parquet..."
	uv run python -m src.main export --output data/export.parquet
	@echo "✅ Parquet export complete"

# Configuration
config:
	@echo "⚙️  Showing current configuration..."
	uv run python -m src.main config

setup-credentials:
	@echo "🔑 Setting up API credentials..."
	@echo "Please edit .env file with your API credentials:"
	@echo ""
	@echo "For Reddit:"
	@echo "  REDDIT_CLIENT_ID=your_client_id"
	@echo "  REDDIT_CLIENT_SECRET=your_client_secret"
	@echo ""
	@echo "For Bluesky:"
	@echo "  BLUESKY_HANDLE=your_handle.bsky.app"
	@echo "  BLUESKY_PASSWORD=your_password"
	@echo ""
	@echo "For Mastodon:"
	@echo "  MASTODON_ACCESS_TOKEN=your_access_token"
	@echo ""
	@echo "Get credentials from:"
	@echo "  Reddit: https://www.reddit.com/prefs/apps"
	@echo "  Bluesky: https://bsky.app"
	@echo "  Mastodon: Your instance settings"

# Quick start
quick-start: setup
	@echo "🚀 Quick start setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Edit .env with your API credentials"
	@echo "2. Run 'make collect-reddit' to test Reddit collection"
	@echo "3. Run 'make stats' to see collected data"
	@echo "4. Run 'make export-json' to export your data"

# Testing
test:
	@echo "🧪 Running test suite..."
	uv run pytest

test-cov:
	@echo "🧪 Running tests with coverage..."
	uv run pytest --cov=src --cov-report=html --cov-report=term
	@echo "📊 Coverage report generated in htmlcov/"

test-fast:
	@echo "🧪 Running fast tests (excluding slow tests)..."
	uv run pytest -m "not slow"

test-database:
	@echo "🧪 Running database tests..."
	uv run pytest tests/test_database.py -v

test-concurrency:
	@echo "🧪 Running concurrency tests..."
	uv run pytest tests/test_concurrency.py -v

test-integration:
	@echo "🧪 Running integration tests..."
	uv run pytest tests/test_integration.py -v

