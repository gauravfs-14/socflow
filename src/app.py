"""Main SocFlow application."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from tqdm import tqdm

from .collectors.reddit import RedditCollector
from .collectors.bluesky import BlueskyCollector
from .collectors.mastodon import MastodonCollector
from .config.settings import Settings, load_settings, save_user_config
from .database.factory import create_database_manager
from .utils.logger import setup_logger


class SocFlowApp:
    """Main SocFlow application class."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize SocFlow application.
        
        Args:
            config_path: Path to configuration file
        """
        self.settings = load_settings(config_path)
        self.logger = setup_logger(self.settings.app.log_level)
        self.db_manager = None
        self.collectors = {}
        self._setup_database()
        self._setup_collectors()
    
    def _setup_database(self) -> None:
        """Setup database manager."""
        try:
            self.db_manager = create_database_manager(self.settings.database)
            self.logger.info(f"Database manager created: {self.settings.database.type}")
        except Exception as e:
            self.logger.error(f"Failed to setup database: {e}")
            raise
    
    def _setup_collectors(self) -> None:
        """Setup data collectors."""
        # Reddit collector
        if self.settings.collectors.reddit.enabled:
            try:
                reddit_config = self.settings.collectors.reddit.dict()
                self.collectors["reddit"] = RedditCollector(reddit_config)
                self.logger.info("Reddit collector initialized")
            except Exception as e:
                self.logger.warning(f"Reddit collector disabled: {e}")
                self.settings.collectors.reddit.enabled = False
        
        # Bluesky collector
        if self.settings.collectors.bluesky.enabled:
            try:
                bluesky_config = self.settings.collectors.bluesky.dict()
                self.collectors["bluesky"] = BlueskyCollector(bluesky_config)
                self.logger.info("Bluesky collector initialized")
            except Exception as e:
                self.logger.warning(f"Bluesky collector disabled: {e}")
                self.settings.collectors.bluesky.enabled = False
        
        # Mastodon collector
        if self.settings.collectors.mastodon.enabled:
            try:
                mastodon_config = self.settings.collectors.mastodon.dict()
                self.collectors["mastodon"] = MastodonCollector(mastodon_config)
                self.logger.info("Mastodon collector initialized")
            except Exception as e:
                self.logger.warning(f"Mastodon collector disabled: {e}")
                self.settings.collectors.mastodon.enabled = False
    
    def create_tables(self) -> None:
        """Create database tables."""
        if not self.db_manager:
            raise RuntimeError("Database manager not initialized")
        
        platforms = list(self.collectors.keys())
        self.db_manager.create_tables(platforms)
        self.logger.info(f"Created tables for platforms: {platforms}")
    
    def collect_data(self, platforms: Optional[List[str]] = None, **kwargs) -> Dict[str, int]:
        """Collect data from specified platforms.
        
        Args:
            platforms: List of platforms to collect from. If None, collects from all enabled platforms.
            **kwargs: Platform-specific collection parameters
            
        Returns:
            Dictionary with platform names and number of collected posts
        """
        if platforms is None:
            platforms = list(self.collectors.keys())
        
        if not self.collectors:
            self.logger.warning("No collectors available. Please check your API credentials.")
            return {}
        
        results = {}
        
        for platform in platforms:
            if platform not in self.collectors:
                self.logger.warning(f"Collector for platform '{platform}' not found")
                continue
            
            collector = self.collectors[platform]
            if not collector.is_enabled():
                self.logger.info(f"Collector for platform '{platform}' is disabled")
                continue
            
            try:
                self.logger.info(f"Starting data collection from {platform}")
                posts = collector.collect(**kwargs)
                
                if posts:
                    self.db_manager.insert_posts(posts)
                    results[platform] = len(posts)
                    self.logger.info(f"Collected {len(posts)} posts from {platform}")
                else:
                    results[platform] = 0
                    self.logger.warning(f"No posts collected from {platform}")
                
            except Exception as e:
                self.logger.error(f"Error collecting from {platform}: {e}")
                results[platform] = 0
        
        return results
    
    def collect_continuously(self, platforms: Optional[List[str]] = None, **kwargs) -> None:
        """Collect data continuously until interrupted.
        
        Args:
            platforms: List of platforms to collect from. If None, collects from all enabled platforms.
            **kwargs: Platform-specific collection parameters
        """
        if platforms is None:
            platforms = list(self.collectors.keys())
        
        if not self.collectors:
            self.logger.warning("No collectors available. Please check your API credentials.")
            return
        
        import signal
        import time
        
        # Track total collected posts
        total_collected = {platform: 0 for platform in platforms}
        
        def signal_handler(signum, frame):
            self.logger.info("Received interrupt signal. Gracefully shutting down...")
            self.logger.info(f"Total posts collected: {sum(total_collected.values())}")
            for platform, count in total_collected.items():
                if count > 0:
                    self.logger.info(f"  {platform}: {count} posts")
            self.close()
            exit(0)
        
        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        self.logger.info("Starting continuous data collection...")
        self.logger.info("Press Ctrl+C to stop and save remaining data")
        
        import threading
        import queue
        
        # Create a queue for collecting posts from all platforms
        posts_queue = queue.Queue()
        
        def collect_from_platform(platform, collector, kwargs):
            """Collect posts from a single platform in a separate thread."""
            self.logger.info(f"Starting continuous collection for {platform}")
            while True:
                try:
                    if not collector.is_enabled():
                        self.logger.warning(f"Collector {platform} is disabled, waiting...")
                        time.sleep(5)
                        continue
                    
                    # Collect a batch of posts
                    self.logger.debug(f"Collecting from {platform}...")
                    posts = collector.collect_continuous(**kwargs)
                    
                    if posts:
                        posts_queue.put((platform, posts))
                        self.logger.info(f"Collected {len(posts)} posts from {platform}")
                    else:
                        self.logger.debug(f"No posts collected from {platform}")
                    
                    # Small delay between collections to avoid rate limiting
                    time.sleep(5)
                    
                except Exception as e:
                    self.logger.error(f"Error collecting from {platform}: {e}")
                    time.sleep(10)  # Wait longer on error
        
        # Start collection threads for each platform
        threads = []
        for platform in platforms:
            if platform in self.collectors:
                collector = self.collectors[platform]
                if collector.is_enabled():
                    thread = threading.Thread(
                        target=collect_from_platform,
                        args=(platform, collector, kwargs),
                        daemon=False
                    )
                    thread.start()
                    threads.append(thread)
                    self.logger.info(f"Started collection thread for {platform}")
        
        if not threads:
            self.logger.warning("No active collection threads started")
            return
        
        try:
            while True:
                try:
                    # Get posts from any platform
                    platform, posts = posts_queue.get(timeout=10)
                    
                    if posts:
                        # Store original count for deduplication reporting
                        original_count = len(posts)
                        self.db_manager.insert_posts(posts)
                        
                        # Note: The actual number of inserted posts will be logged by the database manager
                        # We'll update our count based on the database response
                        total_collected[platform] += original_count
                        self.logger.info(f"📊 Processed {original_count} posts from {platform} (Total processed: {total_collected[platform]})")
                    else:
                        self.logger.debug(f"No posts to save from {platform}")
                    
                except queue.Empty:
                    # No posts received in timeout period, continue
                    self.logger.debug("No posts received in timeout period, continuing...")
                    continue
                    
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal. Gracefully shutting down...")
            # Wait for threads to finish
            for thread in threads:
                thread.join(timeout=5)
            signal_handler(signal.SIGINT, None)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics.
        
        Returns:
            Dictionary with collection statistics
        """
        if not self.db_manager:
            return {}
        
        stats = {
            "total_posts": self.db_manager.get_post_count(),
            "by_platform": {}
        }
        
        for platform in self.collectors.keys():
            count = self.db_manager.get_post_count(platform)
            stats["by_platform"][platform] = count
        
        return stats
    
    def export_data(self, output_path: str, platform: Optional[str] = None) -> None:
        """Export data to file.
        
        Args:
            output_path: Path to output file
            platform: Platform to export. If None, exports all platforms.
        """
        if not self.db_manager:
            raise RuntimeError("Database manager not initialized")
        
        posts = self.db_manager.get_posts(platform=platform)
        
        if not posts:
            self.logger.warning("No data to export")
            return
        
        # Create output directory if it doesn't exist
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Export based on file extension
        if output_path.suffix == ".json":
            import json
            with open(output_path, 'w') as f:
                json.dump(posts, f, indent=2, default=str)
        elif output_path.suffix == ".csv":
            import pandas as pd
            df = pd.DataFrame(posts)
            df.to_csv(output_path, index=False)
        elif output_path.suffix == ".parquet":
            try:
                import pyarrow
            except ImportError:
                raise ImportError(
                    "pyarrow is required for Parquet export. "
                    "Install it with: pip install pyarrow or pip install socflow[parquet]"
                )
            import pandas as pd
            df = pd.DataFrame(posts)
            df.to_parquet(output_path, index=False)
        else:
            raise ValueError(f"Unsupported file format: {output_path.suffix}")
        
        self.logger.info(f"Exported {len(posts)} posts to {output_path}")
    
    def close(self) -> None:
        """Close application and cleanup resources."""
        if self.db_manager:
            self.db_manager.close()
        self.logger.info("Application closed")


@click.group()
@click.option('--config', '-c', help='Path to configuration file')
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.pass_context
def cli(ctx, config, debug):
    """SocFlow - Social media data collection framework."""
    ctx.ensure_object(dict)
    ctx.obj['config'] = config
    ctx.obj['debug'] = debug


@cli.command()
@click.option('--platforms', '-p', multiple=True, help='Platforms to collect from')
@click.option('--subreddits', multiple=True, help='Reddit subreddits to collect from')
@click.option('--keywords', multiple=True, help='Bluesky keywords to search for')
@click.option('--hashtags', multiple=True, help='Mastodon hashtags to search for')
@click.option('--instances', multiple=True, help='Mastodon instances to collect from')
@click.pass_context
def collect(ctx, platforms, subreddits, keywords, hashtags, instances):
    """Collect data from social media platforms."""
    app = SocFlowApp(ctx.obj['config'])
    
    try:
        # Create tables if they don't exist
        app.create_tables()
        
        # Prepare collection parameters
        kwargs = {}
        if subreddits:
            kwargs['subreddits'] = list(subreddits)
        if keywords:
            kwargs['keywords'] = list(keywords)
        if hashtags:
            kwargs['hashtags'] = list(hashtags)
        if instances:
            kwargs['instances'] = list(instances)
        
        # Collect data
        results = app.collect_data(platforms=list(platforms) if platforms else None, **kwargs)
        
        # Display results
        if not results:
            click.echo("❌ No data collected. Please check your API credentials.")
            click.echo("Run 'make setup-env' to configure your credentials.")
        else:
            click.echo("Collection Results:")
            for platform, count in results.items():
                click.echo(f"  {platform}: {count} posts")
        
        # Show total stats
        stats = app.get_stats()
        click.echo(f"\nTotal posts in database: {stats['total_posts']}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
    finally:
        app.close()


@cli.command()
@click.option('--platforms', '-p', multiple=True, help='Platforms to collect from')
@click.option('--subreddits', multiple=True, help='Reddit subreddits to collect from')
@click.option('--keywords', multiple=True, help='Bluesky keywords to search for')
@click.option('--hashtags', multiple=True, help='Mastodon hashtags to search for')
@click.option('--instances', multiple=True, help='Mastodon instances to collect from')
@click.pass_context
def collect_continuous(ctx, platforms, subreddits, keywords, hashtags, instances):
    """Collect data continuously until interrupted."""
    app = SocFlowApp(ctx.obj['config'])
    
    try:
        # Create tables if they don't exist
        app.create_tables()
        
        # Prepare collection parameters
        kwargs = {}
        if subreddits:
            kwargs['subreddits'] = list(subreddits)
        if keywords:
            kwargs['keywords'] = list(keywords)
        if hashtags:
            kwargs['hashtags'] = list(hashtags)
        if instances:
            kwargs['instances'] = list(instances)
        
        # Start continuous collection
        app.collect_continuously(platforms=list(platforms) if platforms else None, **kwargs)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
    finally:
        app.close()


@cli.command()
@click.option('--platform', '-p', help='Platform to show stats for')
@click.pass_context
def stats(ctx, platform):
    """Show collection statistics."""
    app = SocFlowApp(ctx.obj['config'])
    
    try:
        stats = app.get_stats()
        
        click.echo("Collection Statistics:")
        click.echo(f"  Total posts: {stats['total_posts']}")
        
        if platform:
            count = stats['by_platform'].get(platform, 0)
            click.echo(f"  {platform}: {count} posts")
        else:
            for platform_name, count in stats['by_platform'].items():
                click.echo(f"  {platform_name}: {count} posts")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
    finally:
        app.close()


@cli.command()
@click.option('--output', '-o', required=True, help='Output file path')
@click.option('--platform', '-p', help='Platform to export')
@click.pass_context
def export(ctx, output, platform):
    """Export collected data."""
    app = SocFlowApp(ctx.obj['config'])
    
    try:
        app.export_data(output, platform)
        click.echo(f"Data exported to {output}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
    finally:
        app.close()


@cli.group()
@click.pass_context
def config(ctx):
    """Manage configuration."""
    pass


@config.command()
@click.pass_context
def show(ctx):
    """Show current configuration."""
    app = SocFlowApp(ctx.obj['config'])
    
    try:
        click.echo("Current Configuration:")
        click.echo(f"  App: {app.settings.app.name}")
        click.echo(f"  Database: {app.settings.database.type}")
        click.echo(f"  Separate databases: {app.settings.database.separate_databases}")
        click.echo(f"  Output directory: {app.settings.app.output_dir}")
        
        click.echo("\nCollectors:")
        for name, collector in app.collectors.items():
            status = "enabled" if collector.is_enabled() else "disabled"
            click.echo(f"  {name}: {status}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
    finally:
        app.close()


@config.command()
@click.option('--path', '-p', help='Path to save config file (default: ./socflow.yml)')
@click.pass_context
def init(ctx, path):
    """Initialize configuration file in current directory."""
    from pathlib import Path
    import yaml
    
    # Try to load default settings from file system (development mode)
    config_data = None
    default_config_path = Path(__file__).parent.parent.parent / "config" / "settings.default.yml"
    
    if default_config_path.exists():
        try:
            with open(default_config_path, 'r') as f:
                config_data = yaml.safe_load(f)
        except Exception:
            pass
    
    # If not found, create default config
    if config_data is None:
        config_data = {
            'app': {
                'name': 'SocFlow',
                'output_dir': 'data',
                'log_level': 'INFO',
                'debug': False
            },
            'database': {
                'type': 'sqlite',
                'path': 'data/socflow.db',
                'separate_databases': False
            },
            'collectors': {
                'reddit': {
                    'enabled': True,
                    'subreddits': ['all'],
                    'user_agent': 'SocFlow/1.0',
                    'max_posts_per_subreddit': 1000,
                    'sort_by': 'hot',
                    'time_filter': 'day'
                },
                'bluesky': {
                    'enabled': True,
                    'max_posts': 1000,
                    'keywords': []
                },
                'mastodon': {
                    'enabled': True,
                    'instances': ['https://mastodon.social'],
                    'max_posts_per_instance': 1000,
                    'hashtags': []
                }
            }
        }
    
    # Determine output path
    if path:
        output_path = Path(path)
    else:
        cwd = Path.cwd()
        output_path = cwd / "socflow.yml"
    
    # Check if file already exists
    if output_path.exists():
        if not click.confirm(f"Config file {output_path} already exists. Overwrite?"):
            click.echo("Cancelled.")
            return
    
    # Save config
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        yaml.dump(config_data, f, default_flow_style=False, indent=2)
    
    click.echo(f"✅ Configuration file created at {output_path}")
    click.echo("💡 Edit the file to configure API credentials and collection settings.")


@config.command()
@click.argument('key')
@click.argument('value')
@click.option('--path', '-p', help='Path to config file (default: ./socflow.yml)')
@click.pass_context
def set(ctx, key, value, path):
    """Set a configuration value.
    
    Examples:
        socflow config set app.log_level DEBUG
        socflow config set database.path ./mydata/socflow.db
        socflow config set collectors.reddit.enabled false
    """
    from pathlib import Path
    import yaml
    
    # Determine config path
    if path:
        config_path = Path(path)
    else:
        cwd = Path.cwd()
        config_path = cwd / "socflow.yml"
    
    if not config_path.exists():
        click.echo(f"❌ Config file not found: {config_path}")
        click.echo("💡 Run 'socflow config init' to create a config file.")
        return
    
    # Load existing config
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f) or {}
    
    # Set nested key (e.g., "app.log_level" -> config_data['app']['log_level'])
    keys = key.split('.')
    current = config_data
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]
    
    # Convert value to appropriate type
    final_key = keys[-1]
    if value.lower() in ('true', 'false'):
        value = value.lower() == 'true'
    elif value.isdigit():
        value = int(value)
    elif value.replace('.', '', 1).isdigit():
        value = float(value)
    
    current[final_key] = value
    
    # Save config
    with open(config_path, 'w') as f:
        yaml.dump(config_data, f, default_flow_style=False, indent=2)
    
    click.echo(f"✅ Set {key} = {value}")
    click.echo(f"💡 Updated {config_path}")


@config.command()
@click.option('--path', '-p', help='Path to config file (default: ./socflow.yml)')
@click.pass_context
def edit(ctx, path):
    """Edit configuration file in default editor."""
    import os
    import subprocess
    from pathlib import Path
    
    # Determine config path
    if path:
        config_path = Path(path)
    else:
        cwd = Path.cwd()
        config_path = cwd / "socflow.yml"
    
    if not config_path.exists():
        click.echo(f"❌ Config file not found: {config_path}")
        click.echo("💡 Run 'socflow config init' to create a config file.")
        return
    
    # Get editor from environment or use default
    editor = os.environ.get('EDITOR', 'nano')
    
    try:
        subprocess.run([editor, str(config_path)])
        click.echo(f"✅ Configuration file edited: {config_path}")
    except FileNotFoundError:
        click.echo(f"❌ Editor '{editor}' not found.")
        click.echo(f"💡 Set EDITOR environment variable or edit manually: {config_path}")


@cli.command()
@click.pass_context
def tui(ctx):
    """Launch the Terminal User Interface for data collection."""
    from .tui import SocFlowTUI
    
    tui = SocFlowTUI(ctx.obj.get('config'))
    tui.run()


if __name__ == "__main__":
    cli()
