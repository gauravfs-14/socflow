# ScoFlow: Unified Multiplatform Data Collection Framework

Product Requirements Document (PRD)

## 1. Overview

ScoFlow is a unified data collection framework designed to aggregate content from Bluesky, Mastodon, Reddit, and major news sources. The system operates as both a CLI and a TUI application. It supports controlled data collection across time ranges, keywords, hashtags, and subcommunities. The application centralizes ingestion logic, applies standard validation using Pydantic models, removes duplicates, and stores results in a combined database schema suitable for downstream machine learning and analytics workflows.

ScoFlow focuses on reliability, modularity, ease of extension, and observable real-time progress. It can run batch-mode data collection or continuous background ingestion within a terminal-friendly interface.

## 2. Goals and Success Criteria

### 2.1 Goals

1. Provide a single tool that collects consistent, labeled, and deduplicated content across multiple social and news platforms.
2. Expose both CLI and TUI interfaces for flexible operation.
3. Enable power users to automate large batch extractions and long-running background jobs.
4. Offer unified data schemas and Pydantic-based validation.
5. Ensure modular collector architecture so that new platforms can be added without breaking the core system.

### 2.2 Success Metrics

1. High reliability across long-running jobs.
2. Runtime performance that improves with parallel execution.
3. Zero externally visible duplication across completed collections.
4. End users able to complete core tasks without consulting documentation.

## 3. Target Users

1. Researchers collecting text corpora from multiple platforms.
2. Data engineers who need batch collection with filters and scheduling.
3. Developers who require a programmable CLI and clean database schema for downstream tasks.
4. Students and analysts who want a user-friendly TUI that shows real-time status and progress bars.

## 4. Key Features

### 4.1 CLI Interface

* Invoke platform collectors using subcommands.
* Pass flags for date ranges, keyword filters, hashtag filters, subreddits, and API controls.
* Support batch jobs, output redirection, and silent mode for automation.
* Provide structured exit codes for scripting.

### 4.2 TUI Interface

* Real-time progress display for each platform.
* Multiple panels showing request rate, collected items, deduplicated count, retry count, and active workers.
* Configurable refresh rate.
* Background mode that minimizes UI to a single status line.

### 4.3 Platform Collectors

**Bluesky**

* Keyword search with full-text filtering.
* Hashtag filtering.
* Customizable feed endpoints.

**Mastodon**

* Hashtag-based streaming or batch-mode search.
* Instance-aware configuration for rate limits.

**Reddit**

* Subreddit selection.
* Pushshift or API based collection.
* Keyword, flair, and time-range filtering.

**News Sources**

* Generic keyword search across supported news APIs or RSS feeds.
* Domain-based filtering.
* Optional historical search windows.

### 4.4 De-duplication Engine

* Fingerprinting algorithm based on hash of text content and URL.
* Guaranteed cross-platform deduplication.
* Accuracy validated with Pydantic models before insertion.

### 4.5 Data Models and Validation

* Pydantic BaseModel for each platform with a shared superclass.
* Strict field validation for timestamps, IDs, authors, and body text.
* Normalized internal schema:

  * `platform`
  * `id`
  * `author`
  * `content`
  * `timestamp`
  * `metadata`

### 4.6 Combined Database

* SQLite or Turso supported.
* Unified table for all platforms with platform-specific metadata stored as JSON.
* Indexing across time, platform, and keywords.
* Migration-ready schema versioning.

### 4.7 Parallel Execution

* Configurable worker count.
* Async collectors for Bluesky and Mastodon.
* Threaded or process-based workers for Reddit and news APIs.
* Execution scheduler that respects rate limits.

### 4.8 Real-Time Updates

* Per-worker logs.
* Metrics panel with throughput, success rate, queue backlog, and estimated time remaining.
* Alerts for rate-limit slowdowns or API errors.

### 4.9 Background Processing

* Detachable TUI session.
* Logs streamed to a file.
* CLI flags for background or daemon-like mode.

### 4.10 Customizability and Configuration

* YAML- or TOML-based configuration files.
* Environment variable overrides for API keys.
* User-level config directory.
* Plugin interface for adding new collectors.

## 5. Non-Functional Requirements

### 5.1 Performance

* Able to process at least 20 requests per second in parallel mode under optimal API limits.
* Indexed database writes achieving less than 5 ms latency.

### 5.2 Reliability

* Automatic retries with exponential backoff.
* Graceful shutdown and resume.
* Checkpointing for long jobs.

### 5.3 Security

* API tokens stored in user config directories.
* No transmission of secrets in logs.
* Optional encrypted storage.

### 5.4 Usability

* Clear error messages.
* Step-by-step installer.
* Inline help for every CLI subcommand.

## 6. System Architecture

### 6.1 High-Level Structure

* Core engine orchestrating tasks.
* Collector modules per platform.
* Pydantic validation layer.
* Deduplicate module.
* Database adapter layer.
* CLI/TUI presentation layer.

### 6.2 Data Flow

1. CLI or TUI issues a collection command.
2. Task scheduler initializes workers.
3. Collectors produce records.
4. Validation layer cleans each record.
5. Deduplication checks consistent fingerprints.
6. Clean items are written to the database.
7. TUI shows real-time metrics.

## 7. Requirements Breakdown

### 7.1 Must Have

* CLI interface with full filtering support.
* TUI with real-time progress.
* Unified database schema.
* Deduplication at insert time.
* Parallel workers.
* Full Pydantic validation.

### 7.2 Should Have

* Configurable scheduling and background mode.
* Structured logs.

### 7.3 Could Have

* Export to JSON, CSV, and Parquet.
* Minimal web-based dashboard.

## 8. Milestones

1. Core CLI interface.
2. Pydantic validation and schema.
3. Storage engine and deduplication.
4. Platform collectors (Bluesky, Reddit, News).
5. TUI implementation.
6. Parallel job engine.
7. Mastodon collector.
8. Documentation and examples.
