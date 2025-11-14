#!/usr/bin/env python3
"""TUI (Terminal User Interface) for SocFlow data collection."""

import asyncio
import multiprocessing
import signal
import subprocess
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor

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
        # Thread-safe data structures for Python 3.14 (GIL removed)
        import threading
        self._stats_lock = threading.Lock()  # Lock for thread-safe stats updates
        
        self.collection_stats = {
            'reddit': {'posts': 0, 'status': 'Starting...', 'last_update': None},
            'bluesky': {'posts': 0, 'status': 'Starting...', 'last_update': None},
            'mastodon': {'posts': 0, 'status': 'Starting...', 'last_update': None}
        }
        self.total_posts = 0
        self.last_db_update = {}  # Cache for database counts
        self.db_update_interval = 10  # Update database counts every 10 seconds
        
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
        """Update collection statistics (thread-safe for Python 3.14)."""
        # Thread-safe update of shared statistics
        with self._stats_lock:
            # Update database count only if enough time has passed (to reduce DB queries)
            current_time = datetime.now()
            should_update_db = (
                platform not in self.last_db_update or 
                (current_time - self.last_db_update[platform]).seconds >= self.db_update_interval
            )
            
            if should_update_db:
                try:
                    # Database query is thread-safe (handled by database manager)
                    db_count = self.app.db_manager.get_post_count(platform)
                    self.collection_stats[platform]['posts'] = db_count
                    self.last_db_update[platform] = current_time
                except:
                    # Fallback to cumulative count if database query fails
                    self.collection_stats[platform]['posts'] += posts
            else:
                # Use cached count for faster updates
                pass
                
            self.collection_stats[platform]['status'] = status
            self.collection_stats[platform]['last_update'] = current_time
            self.total_posts = sum(stats['posts'] for stats in self.collection_stats.values())
    
    async def _collect_platform(self, platform: str, collector, kwargs: Dict[str, Any]):
        """Collect data from a specific platform asynchronously."""
        while self.running:
            try:
                if not collector.is_enabled():
                    self._update_stats(platform, 0, "Disabled - No credentials")
                    await asyncio.sleep(5)
                    continue
                
                # Update status to show we're starting collection
                self._update_stats(platform, 0, "Collecting...")
                
                # Collect posts with timeout handling using thread pool for CPU-bound work
                try:
                    loop = asyncio.get_event_loop()
                    with ThreadPoolExecutor() as executor:
                        posts = await loop.run_in_executor(
                            executor, 
                            collector.collect_continuous, 
                            **kwargs
                        )
                except Exception as e:
                    print(f"Collection error for {platform}: {e}")
                    posts = []
                
                if posts:
                    # Save to database
                    self.app.db_manager.insert_posts(posts)
                    self._update_stats(platform, len(posts), f"Active - {len(posts)} posts")
                else:
                    self._update_stats(platform, 0, "Active - No new posts")
                
                # Small delay between collections
                await asyncio.sleep(10)
                
            except Exception as e:
                self._update_stats(platform, 0, f"Error: {str(e)[:30]}...")
                await asyncio.sleep(10)  # Wait longer on error
    
    async def _start_collection_tasks(self):
        """Start collection tasks for all platforms using asyncio."""
        tasks = []
        
        # Reddit task
        if 'reddit' in self.app.collectors:
            reddit_task = asyncio.create_task(
                self._collect_platform('reddit', self.app.collectors['reddit'], {'subreddits': ['all']})
            )
            tasks.append(reddit_task)
        
        # Bluesky task
        if 'bluesky' in self.app.collectors:
            bluesky_task = asyncio.create_task(
                self._collect_platform('bluesky', self.app.collectors['bluesky'], {})
            )
            tasks.append(bluesky_task)
        
        # Mastodon task
        if 'mastodon' in self.app.collectors:
            mastodon_task = asyncio.create_task(
                self._collect_platform('mastodon', self.app.collectors['mastodon'], {})
            )
            tasks.append(mastodon_task)
        
        return tasks
    
    def _start_collection_subprocesses(self):
        """Start collection subprocesses for true parallelism using subprocess."""
        processes = []
        
        # Reddit subprocess
        if 'reddit' in self.app.collectors:
            reddit_process = subprocess.Popen([
                'uv', 'run', 'python', '-c', 
                f'''
import sys, os
sys.path.append(os.getcwd())
from src.app import SocFlowApp
app = SocFlowApp()
collector = app.collectors["reddit"]
import json, time
from datetime import datetime
stats_file = "/tmp/socflow_reddit_stats.json"
while True:
    try:
        posts = collector.collect_continuous(subreddits=["all"])
        if posts:
            app.db_manager.insert_posts(posts)
        stats = {{"posts": len(posts), "status": "Active", "last_update": datetime.now().strftime("%H:%M:%S")}}
        with open(stats_file, "w") as f:
            json.dump(stats, f)
        time.sleep(10)
    except Exception as e:
        stats = {{"posts": 0, "status": f"Error: {{str(e)[:30]}}", "last_update": datetime.now().strftime("%H:%M:%S")}}
        with open(stats_file, "w") as f:
            json.dump(stats, f)
        time.sleep(10)
                '''
            ])
            processes.append(('reddit', reddit_process))
        
        # Bluesky subprocess
        if 'bluesky' in self.app.collectors:
            bluesky_process = subprocess.Popen([
                'uv', 'run', 'python', '-c', 
                f'''
import sys, os
sys.path.append(os.getcwd())
from src.app import SocFlowApp
app = SocFlowApp()
collector = app.collectors["bluesky"]
import json, time
from datetime import datetime
stats_file = "/tmp/socflow_bluesky_stats.json"
while True:
    try:
        posts = collector.collect_continuous()
        if posts:
            app.db_manager.insert_posts(posts)
        stats = {{"posts": len(posts), "status": "Active", "last_update": datetime.now().strftime("%H:%M:%S")}}
        with open(stats_file, "w") as f:
            json.dump(stats, f)
        time.sleep(10)
    except Exception as e:
        stats = {{"posts": 0, "status": f"Error: {{str(e)[:30]}}", "last_update": datetime.now().strftime("%H:%M:%S")}}
        with open(stats_file, "w") as f:
            json.dump(stats, f)
        time.sleep(10)
                '''
            ])
            processes.append(('bluesky', bluesky_process))
        
        # Mastodon subprocess
        if 'mastodon' in self.app.collectors:
            mastodon_process = subprocess.Popen([
                'uv', 'run', 'python', '-c', 
                f'''
import sys, os
sys.path.append(os.getcwd())
from src.app import SocFlowApp
app = SocFlowApp()
collector = app.collectors["mastodon"]
import json, time
from datetime import datetime
stats_file = "/tmp/socflow_mastodon_stats.json"
while True:
    try:
        posts = collector.collect_continuous()
        if posts:
            app.db_manager.insert_posts(posts)
        stats = {{"posts": len(posts), "status": "Active", "last_update": datetime.now().strftime("%H:%M:%S")}}
        with open(stats_file, "w") as f:
            json.dump(stats, f)
        time.sleep(10)
    except Exception as e:
        stats = {{"posts": 0, "status": f"Error: {{str(e)[:30]}}", "last_update": datetime.now().strftime("%H:%M:%S")}}
        with open(stats_file, "w") as f:
            json.dump(stats, f)
        time.sleep(10)
                '''
            ])
            processes.append(('mastodon', mastodon_process))
        
        return processes
    
    def _collect_platform_process(self, platform: str, kwargs: Dict[str, Any]):
        """Collect data from a platform in a separate process for true parallelism."""
        # Import here to avoid issues with multiprocessing
        from src.app import SocFlowApp
        
        # Create a new app instance in this process
        app = SocFlowApp()
        collector = app.collectors.get(platform)
        
        if not collector or not collector.is_enabled():
            return
        
        # Create a shared memory manager for stats
        manager = multiprocessing.Manager()
        stats_dict = manager.dict()
        
        # Initialize stats
        stats_dict.update({
            'posts': 0,
            'status': 'Starting...',
            'last_update': datetime.now().strftime('%H:%M:%S')
        })
        
        # Store stats in a way the main process can access
        # For now, we'll use a simple file-based approach
        import json
        import os
        
        stats_file = f"/tmp/socflow_{platform}_stats.json"
        
        while True:
            try:
                # Update status
                stats_dict['status'] = 'Collecting...'
                stats_dict['last_update'] = datetime.now().strftime('%H:%M:%S')
                
                # Collect posts
                posts = collector.collect_continuous(**kwargs)
                
                if posts:
                    # Save to database
                    app.db_manager.insert_posts(posts)
                    stats_dict['posts'] += len(posts)
                    stats_dict['status'] = f'Active - {len(posts)} posts'
                else:
                    stats_dict['status'] = 'Active - No new posts'
                
                # Write stats to file
                with open(stats_file, 'w') as f:
                    json.dump(dict(stats_dict), f)
                
                # Small delay between collections
                time.sleep(10)
                
            except Exception as e:
                stats_dict['status'] = f'Error: {str(e)[:30]}...'
                with open(stats_file, 'w') as f:
                    json.dump(dict(stats_dict), f)
                time.sleep(10)
    
    def _load_process_stats(self, platform: str):
        """Load stats from a process via file."""
        import json
        import os
        
        stats_file = f"/tmp/socflow_{platform}_stats.json"
        
        if os.path.exists(stats_file):
            try:
                with open(stats_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            'posts': 0,
            'status': 'Starting...',
            'last_update': 'N/A'
        }
    
    def _start_collection_threads(self):
        """Start collection threads for all platforms.
        
        With Python 3.14's GIL removal, these threads run truly concurrently
        on separate CPU cores, enabling true parallelism for both I/O and CPU-bound tasks.
        """
        import threading
        threads = []
        
        # Reddit thread
        if 'reddit' in self.app.collectors:
            reddit_thread = threading.Thread(
                target=self._collect_platform_sync,
                args=('reddit', self.app.collectors['reddit'], {'subreddits': ['all']}),
                daemon=True
            )
            reddit_thread.start()
            threads.append(reddit_thread)
        
        # Bluesky thread
        if 'bluesky' in self.app.collectors:
            bluesky_thread = threading.Thread(
                target=self._collect_platform_sync,
                args=('bluesky', self.app.collectors['bluesky'], {}),
                daemon=True
            )
            bluesky_thread.start()
            threads.append(bluesky_thread)
        
        # Mastodon thread
        if 'mastodon' in self.app.collectors:
            mastodon_thread = threading.Thread(
                target=self._collect_platform_sync,
                args=('mastodon', self.app.collectors['mastodon'], {}),
                daemon=True
            )
            mastodon_thread.start()
            threads.append(mastodon_thread)
        
        return threads
    
    def _collect_platform_sync(self, platform: str, collector, kwargs: Dict[str, Any]):
        """Synchronous version of platform collection for threading."""
        while self.running:
            try:
                if not collector.is_enabled():
                    self._update_stats(platform, 0, "Disabled - No credentials")
                    time.sleep(5)
                    continue
                
                # Update status to show we're starting collection
                self._update_stats(platform, 0, "Collecting...")
                
                # Collect posts with timeout handling
                try:
                    posts = collector.collect_continuous(**kwargs)
                except Exception as e:
                    print(f"Collection error for {platform}: {e}")
                    posts = []
                
                if posts:
                    # Save to database
                    self.app.db_manager.insert_posts(posts)
                    self._update_stats(platform, len(posts), f"Active - {len(posts)} posts")
                else:
                    self._update_stats(platform, 0, "Active - No new posts")
                
                # Small delay between collections
                time.sleep(10)
                
            except Exception as e:
                self._update_stats(platform, 0, f"Error: {str(e)[:30]}...")
                time.sleep(10)  # Wait longer on error
    
    def run(self):
        """Run the TUI with threading (I/O-bound parallelism)."""
        try:
            # Start collection threads (works well for I/O-bound operations)
            threads = self._start_collection_threads()
            
            if not threads:
                self.console.print("[red]No collectors available. Please check your API credentials.[/red]")
                return
            
            self.console.print("[green]🚀 Starting collection with true concurrency (Python 3.14+ GIL removed)![/green]")
            self.console.print("[yellow]Threads run truly concurrently across CPU cores.[/yellow]")
            
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
    # Required for multiprocessing on some systems
    multiprocessing.set_start_method('spawn', force=True)
    
    import argparse
    
    parser = argparse.ArgumentParser(description="SocFlow TUI for data collection")
    parser.add_argument('--config', '-c', type=str, help='Path to configuration file')
    args = parser.parse_args()
    
    tui = SocFlowTUI(args.config)
    tui.run()


if __name__ == "__main__":
    main()
