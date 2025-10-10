# 🧩 SocFlow

**SocFlow** is a unified framework for collecting and analyzing public discourse from multiple social platforms such as **Reddit**, **Bluesky**, and **Mastodon**.  
It helps researchers and developers build large-scale social datasets for sentiment analysis, topic modeling, and behavioral studies.

## 🚀 Features

- Collect data from multiple public APIs (Reddit, Bluesky, Mastodon)
- Unified schema for all platforms
- Configurable keywords, subreddits, and hashtags
- Supports **SQLite** and **Parquet** storage backends
- CLI-based, modular, and easily extensible

## ⚙️ Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/socflow.git
cd socflow

# (Optional) Create a virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv sync
```

## 🧠 Quick Start

1. Copy the example config:

   ```bash
   cp config/settings.example.yaml config/settings.yaml
   ```

2. Set environment variables in `.env` for API keys.

3. Run any collector:

   ```bash
   socflow reddit --subreddit all
   socflow mastodon --instance mastodon.social
   socflow bluesky
   ```

Data will be stored in `data/socflow.db` or `data/socflow.parquet`.

## 🧩 Configuration

All settings are defined in `config/settings.yaml`:

```yaml
collectors:
  reddit:
    enabled: true
    subreddits: ["all", "MachineLearning"]
  bluesky:
    enabled: true
  mastodon:
    enabled: true
    instances: ["https://mastodon.social"]
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

## 🧾 License

MIT License © 2025 Gaurab Chhetri
