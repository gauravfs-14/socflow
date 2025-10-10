# 🧩 SocFlow

**SocFlow** is a unified framework for collecting and analyzing public discourse from multiple social platforms such as **Reddit**, **Bluesky**, and **Mastodon**.  
It helps researchers and developers build large-scale social datasets for sentiment analysis, topic modeling, and behavioral studies.

## 🚀 Features

- **Object-Oriented Design**: Clean, modular architecture with reusable components
- **Hierarchical Configuration**: Dev and user-level configuration management
- **Database Flexibility**: Choose between single or separate databases per platform
- **Pydantic Validation**: Type-safe data models with automatic validation
- **Multiple Platforms**: Reddit, Bluesky, and Mastodon support
- **Unified Schema**: Consistent data structure across all platforms
- **CLI Interface**: Easy-to-use command-line interface
- **Export Options**: JSON, CSV, and Parquet export formats

## ⚙️ Installation

### Quick Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/socflow.git
cd socflow

# Complete setup with one command
make setup
```

### Manual Setup

```bash
# Create a virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv sync

# Setup environment and configuration
make setup-env
make setup-config
```

## 🧠 Quick Start

1. **Set up environment variables**:

   ```bash
   cp .env.example .env
   # Edit .env with your API credentials
   ```

2. **Run data collection**:

   ```bash
   # Collect from Reddit
   python -m src.main collect --platforms reddit --subreddits all MachineLearning
   
   # Collect from Bluesky
   python -m src.main collect --platforms bluesky --keywords AI machinelearning
   
   # Collect from Mastodon
   python -m src.main collect --platforms mastodon --hashtags AI tech --instances https://mastodon.social
   
   # Collect from all platforms
   python -m src.main collect --platforms reddit bluesky mastodon
   
   # Show statistics
   python -m src.main stats
   
   # Export data
   python -m src.main export --output data/export.json
   ```

## 🏗️ Architecture

### Configuration Management

- **Dev Config**: `config/settings.yml` - Development settings
- **User Config**: `~/.socflow/config.yml` - User-specific settings
- **Environment Variables**: Override any setting via environment variables

### Database Options

- **Single Database**: All platforms in one database (default)
- **Separate Databases**: One database per platform
- **Supported Types**: SQLite (default), PostgreSQL, MySQL

### Data Models

- **BasePost**: Common interface for all platforms
- **Platform-Specific Models**: RedditPost, BlueskyPost, MastodonPost
- **Pydantic Validation**: Automatic data validation and serialization

## 🧩 Configuration

### Database Configuration

```yaml
database:
  type: "sqlite"  # sqlite, postgresql, mysql
  path: "data/socflow.db"
  separate_databases: false  # true for separate DBs per platform
```

### Reddit Configuration

```yaml
collectors:
  reddit:
    enabled: true
    subreddits: ["all", "MachineLearning"]
    max_posts_per_subreddit: 1000
    sort_by: "hot"  # hot, new, top, rising
    time_filter: "day"  # hour, day, week, month, year, all
```

### Environment Variables

```bash
# Reddit API
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret

# Bluesky
BLUESKY_HANDLE=your_handle.bsky.app
BLUESKY_PASSWORD=your_password

# Mastodon
MASTODON_ACCESS_TOKEN=your_access_token
```

## 🗃️ Unified Schema

Each collected post is normalized into a common structure:

| Field           | Description                             |
| --------------- | --------------------------------------- |
| `platform`      | Source platform (reddit, bluesky, etc.) |
| `object_id`     | Unique ID per platform                  |
| `author_handle` | Username or handle                      |
| `text`          | Post or comment text                    |
| `created_at`    | Timestamp                               |
| `tags`          | Hashtags or communities                 |
| `metrics`       | Likes, shares, upvotes, etc.            |
| `url`           | Link to the original post               |

### Platform-Specific Fields

**Reddit**:

- `subreddit`, `title`, `flair`, `is_self`, `is_nsfw`
- `upvotes`, `downvotes`, `score`, `gilded`

**Bluesky**:

- `handle`, `display_name`, `is_reply`, `is_repost`
- `likes`, `reposts`, `replies`, `quotes`

**Mastodon**:

- `instance`, `is_reblog`, `is_sensitive`
- `favourites`, `reblogs`, `replies`, `bookmarks`

## 🚀 Usage

### Makefile Commands (Recommended)

The project includes a comprehensive Makefile for easy usage:

```bash
# Show all available commands
make help

# Complete project setup
make setup

# Data collection
make collect-reddit      # Collect from Reddit
make collect-bluesky     # Collect from Bluesky  
make collect-mastodon    # Collect from Mastodon
make collect-all         # Collect from all platforms

# Data management
make stats               # Show statistics
make export-json         # Export as JSON
make export-csv          # Export as CSV
make export-parquet      # Export as Parquet

# Development
make test                # Run tests
make lint                # Run linting
make format              # Format code
make clean               # Clean up files

# Configuration
make config              # Show current config
make setup-env           # Setup environment file
```

### CLI Commands

```bash
# Collect data from Reddit
python -m src.main collect --platforms reddit --subreddits all

# Collect data from Bluesky
python -m src.main collect --platforms bluesky --keywords AI machinelearning

# Collect data from Mastodon
python -m src.main collect --platforms mastodon --hashtags AI tech

# Collect from all platforms
python -m src.main collect --platforms reddit bluesky mastodon

# Show statistics
python -m src.main stats --platform reddit

# Export data
python -m src.main export --output data/export.json --platform reddit

# Show configuration
python -m src.main config
```

### Programmatic Usage

```python
from src.app import SocFlowApp

# Initialize app
app = SocFlowApp("config/settings.yml")

# Create tables
app.create_tables()

# Collect data
results = app.collect_data(platforms=["reddit"])

# Get statistics
stats = app.get_stats()

# Export data
app.export_data("data/export.json")

# Cleanup
app.close()
```

## 🔧 Development

### Project Structure

```
src/
├── app.py              # Main application and CLI
├── config/             # Configuration management
│   └── settings.py
├── models/             # Pydantic data models
│   ├── base.py
│   ├── reddit.py
│   ├── bluesky.py
│   └── mastodon.py
├── database/           # Database abstraction
│   ├── base.py
│   ├── sqlite.py
│   └── factory.py
├── collectors/         # Data collectors
│   ├── base.py
│   └── reddit.py
└── utils/              # Utilities
    └── logger.py
```

### Adding New Platforms

1. Create a new collector class inheriting from `BaseCollector`
2. Create platform-specific data models
3. Update the database schema if needed
4. Register the collector in the main application

### Adding New Database Types

1. Create a new database manager inheriting from `DatabaseManager`
2. Implement all abstract methods
3. Update the factory function
4. Add configuration options

## 🧾 License

MIT License © 2025 Gaurab Chhetri
