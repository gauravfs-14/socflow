#!/usr/bin/env python3
"""TUI (Terminal User Interface) for SocFlow data collection."""

import asyncio
import signal
import sys
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.text import Text

from .app import SocFlowApp
from .collectors import BlueskyCollector, MastodonCollector, RedditCollector


class SocFlowTUI:
    """Terminal User Interface for SocFlow data collection."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the TUI."""
        self.console = Console()
        self.app = SocFlowApp(config_path)
        
        # Create database tables
        platforms = list(self.app.collectors.keys())
        self.app.db_manager.create_tables(platforms)
        
        self.layout = Layout()
        self.running = True
        self.collection_stats = {
            'reddit': {'posts': 0, 'status': 'Starting...', 'last_update': None},
            'bluesky': {'posts': 0, 'status': 'Starting...', 'last_update': None},
            'mastodon': {'posts': 0, 'status': 'Starting...', 'last_update': None}
        }
        self.total_posts = 0
        
        # Setup layout
        self._setup_layout()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _setup_layout(self):
        """Setup the TUI layout."""
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        self.layout["main"].split_row(
            Layout(name="reddit", ratio=1),
            Layout(name="bluesky", ratio=1),
            Layout(name="mastodon", ratio=1)
        )
    
    def _signal_handler(self, signum, frame):
        """Handle interrupt signals."""
        self.console.print("\n[yellow]Received interrupt signal. Shutting down gracefully...[/yellow]")
        self.running = False
        self.app.close()
        sys.exit(0)
    
    def _create_header(self) -> Panel:
        """Create the header panel."""
        title = Text("SocFlow - Social Media Data Collection", style="bold blue")
        subtitle = Text(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", style="dim")
        return Panel(Align.center(f"{title}\n{subtitle}"), style="blue")
    
    def _create_footer(self) -> Panel:
        """Create the footer panel."""
        total = sum(stats['posts'] for stats in self.collection_stats.values())
        footer_text = f"Total Posts: {total} | Press Ctrl+C to stop"
        return Panel(Align.center(footer_text), style="green")
    
    def _create_platform_panel(self, platform: str) -> Panel:
        """Create a panel for a specific platform."""
        stats = self.collection_stats[platform]
        
        # Create simple text content
        content = Text()
        content.append(f"Platform: {platform.title()}\n", style="bold blue")
        content.append(f"Status: {stats['status']}\n", style="green" if "Active" in stats['status'] else "yellow")
        content.append(f"Posts: {stats['posts']}\n", style="cyan")
        if stats['last_update']:
            content.append(f"Last Update: {stats['last_update'].strftime('%H:%M:%S')}\n", style="magenta")
        else:
            content.append("Last Update: N/A\n", style="dim")
        
        return Panel(content, title=f"[bold]{platform.title()}[/bold] Collector", border_style="blue")
    
    def _update_stats(self, platform: str, posts: int, status: str):
        """Update collection statistics."""
        self.collection_stats[platform]['posts'] += posts
        self.collection_stats[platform]['status'] = status
        self.collection_stats[platform]['last_update'] = datetime.now()
        self.total_posts = sum(stats['posts'] for stats in self.collection_stats.values())
    
    def _collect_platform(self, platform: str, collector, kwargs: Dict[str, Any]):
        """Collect data from a specific platform in a separate thread."""
        while self.running:
            try:
                if not collector.is_enabled():
                    self._update_stats(platform, 0, "Disabled - No credentials")
                    time.sleep(5)
                    continue
                
                # Update status to show we're starting collection
                self._update_stats(platform, 0, "Collecting...")
                
                # Collect posts
                posts = collector.collect_continuous(**kwargs)
                
                if posts:
                    # Save to database
                    self.app.db_manager.insert_posts(posts)
                    self._update_stats(platform, len(posts), f"Active - {len(posts)} posts")
                else:
                    self._update_stats(platform, 0, "Active - No new posts")
                
                # Small delay between collections
                time.sleep(5)
                
            except Exception as e:
                self._update_stats(platform, 0, f"Error: {str(e)[:30]}...")
                time.sleep(10)  # Wait longer on error
    
    def _start_collection_threads(self):
        """Start collection threads for all platforms."""
        threads = []
        
        # Reddit thread
        if 'reddit' in self.app.collectors:
            reddit_thread = threading.Thread(
                target=self._collect_platform,
                args=('reddit', self.app.collectors['reddit'], {'subreddits': ['all']}),
                daemon=True
            )
            reddit_thread.start()
            threads.append(reddit_thread)
        
        # Bluesky thread
        if 'bluesky' in self.app.collectors:
            bluesky_thread = threading.Thread(
                target=self._collect_platform,
                args=('bluesky', self.app.collectors['bluesky'], {}),
                daemon=True
            )
            bluesky_thread.start()
            threads.append(bluesky_thread)
        
        # Mastodon thread
        if 'mastodon' in self.app.collectors:
            mastodon_thread = threading.Thread(
                target=self._collect_platform,
                args=('mastodon', self.app.collectors['mastodon'], {}),
                daemon=True
            )
            mastodon_thread.start()
            threads.append(mastodon_thread)
        
        return threads
    
    def run(self):
        """Run the TUI."""
        try:
            # Start collection threads
            threads = self._start_collection_threads()
            
            if not threads:
                self.console.print("[red]No collectors available. Please check your API credentials.[/red]")
                return
            
            # Start the live display
            with Live(self.layout, console=self.console, screen=True, refresh_per_second=2) as live:
                while self.running:
                    # Update the layout
                    self.layout["header"].update(self._create_header())
                    self.layout["footer"].update(self._create_footer())
                    self.layout["reddit"].update(self._create_platform_panel("reddit"))
                    self.layout["bluesky"].update(self._create_platform_panel("bluesky"))
                    self.layout["mastodon"].update(self._create_platform_panel("mastodon"))
                    
                    # Refresh the display
                    live.refresh()
                    
                    # Small delay
                    time.sleep(0.5)
        
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Collection stopped by user.[/yellow]")
        except Exception as e:
            self.console.print(f"\n[red]Error: {e}[/red]")
        finally:
            self.app.close()
            self.console.print(f"\n[green]Final Stats:[/green]")
            for platform, stats in self.collection_stats.items():
                self.console.print(f"  {platform.title()}: {stats['posts']} posts")


def main():
    """Main entry point for the TUI."""
    import argparse
    
    parser = argparse.ArgumentParser(description="SocFlow TUI for data collection")
    parser.add_argument('--config', '-c', type=str, help='Path to configuration file')
    args = parser.parse_args()
    
    tui = SocFlowTUI(args.config)
    tui.run()


if __name__ == "__main__":
    main()
