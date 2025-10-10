"""Bluesky data collector."""

import os
from typing import Any, Dict, List, Optional

from atproto import Client, models
from tqdm import tqdm

from ..models.bluesky import BlueskyPost
from .base import BaseCollector


class BlueskyCollector(BaseCollector):
    """Bluesky data collector."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Bluesky collector.
        
        Args:
            config: Bluesky collector configuration
        """
        super().__init__(config)
        self.client = None
        self._setup_client()
    
    def _setup_client(self) -> None:
        """Setup Bluesky client."""
        handle = self.config.get("handle") or os.getenv("BLUESKY_HANDLE")
        password = self.config.get("password") or os.getenv("BLUESKY_PASSWORD")
        
        if not handle or not password:
            raise ValueError("Bluesky credentials not found. Set BLUESKY_HANDLE and BLUESKY_PASSWORD environment variables.")
        
        self.client = Client()
        try:
            self.client.login(handle, password)
        except Exception as e:
            raise ValueError(f"Failed to login to Bluesky: {e}")
    
    def collect(self, keywords: Optional[List[str]] = None, **kwargs) -> List[BlueskyPost]:
        """Collect data from Bluesky.
        
        Args:
            keywords: List of keywords to search for. If None, uses config default.
            **kwargs: Additional collection parameters
            
        Returns:
            List of collected Bluesky posts
        """
        if not self.is_enabled():
            return []
        
        if not self.validate_config():
            raise ValueError("Invalid Bluesky collector configuration")
        
        if keywords is None:
            keywords = self.config.get("keywords", [])
        
        posts = []
        max_posts = self.config.get("max_posts", 1000)
        
        try:
            if keywords:
                # Search by keywords
                for keyword in keywords:
                    keyword_posts = self._search_by_keyword(keyword, max_posts // len(keywords))
                    posts.extend(keyword_posts)
            else:
                # Get timeline posts
                timeline_posts = self._get_timeline_posts(max_posts)
                posts.extend(timeline_posts)
        
        except Exception as e:
            print(f"Error collecting from Bluesky: {e}")
        
        return posts
    
    def collect_continuous(self, keywords: Optional[List[str]] = None, **kwargs) -> List[BlueskyPost]:
        """Collect data continuously from Bluesky.
        
        Args:
            keywords: Optional keywords to filter posts by
            **kwargs: Additional collection parameters
            
        Returns:
            List of collected Bluesky posts
        """
        if not self.is_enabled():
            return []
        
        posts = []
        batch_size = 10
        
        try:
            # For now, just get timeline posts since search API has issues
            # TODO: Fix search API later
            timeline_posts = self._get_timeline_posts(batch_size)
            posts.extend(timeline_posts)
        
        except Exception as e:
            print(f"Error collecting from Bluesky: {e}")
        
        return posts
    
    def _search_by_keyword(self, keyword: str, max_posts: int) -> List[BlueskyPost]:
        """Search posts by keyword.
        
        Args:
            keyword: Keyword to search for
            max_posts: Maximum number of posts to collect
            
        Returns:
            List of posts matching the keyword
        """
        posts = []
        
        try:
            # Search for posts containing the keyword
            search_results = self.client.app.bsky.feed.search_posts(
                q=keyword
            )
            
            for post_data in tqdm(search_results.posts, desc=f"Searching for '{keyword}'"):
                try:
                    post = BlueskyPost.from_atproto_record(post_data)
                    posts.append(post)
                except Exception as e:
                    print(f"Error processing post: {e}")
                    continue
        
        except Exception as e:
            print(f"Error searching for keyword '{keyword}': {e}")
        
        return posts
    
    def _get_timeline_posts(self, max_posts: int) -> List[BlueskyPost]:
        """Get posts from timeline.
        
        Args:
            max_posts: Maximum number of posts to collect
            
        Returns:
            List of timeline posts
        """
        posts = []
        
        try:
            # Get timeline
            timeline = self.client.app.bsky.feed.get_timeline()
            
            for feed_item in tqdm(timeline.feed, desc="Collecting timeline posts"):
                try:
                    if hasattr(feed_item, 'post') and feed_item.post:
                        post = BlueskyPost.from_atproto_record(feed_item.post)
                        posts.append(post)
                except Exception as e:
                    print(f"Error processing timeline post: {e}")
                    continue
        
        except Exception as e:
            print(f"Error getting timeline: {e}")
        
        return posts
    
    def get_user_posts(self, handle: str, max_posts: int = 100) -> List[BlueskyPost]:
        """Get posts from a specific user.
        
        Args:
            handle: User handle (e.g., @user.bsky.app)
            max_posts: Maximum number of posts to collect
            
        Returns:
            List of user posts
        """
        if not self.is_enabled():
            return []
        
        posts = []
        
        try:
            # Get user profile
            profile = self.client.app.bsky.actor.get_profile(actor=handle)
            
            # Get user's posts
            user_posts = self.client.app.bsky.feed.get_author_feed(
                actor=handle,
                limit=max_posts
            )
            
            for feed_item in tqdm(user_posts.feed, desc=f"Collecting posts from {handle}"):
                try:
                    if hasattr(feed_item, 'post') and feed_item.post:
                        post = BlueskyPost.from_atproto_record(feed_item.post.record)
                        posts.append(post)
                except Exception as e:
                    print(f"Error processing user post: {e}")
                    continue
        
        except Exception as e:
            print(f"Error getting posts from user {handle}: {e}")
        
        return posts
    
    def validate_config(self) -> bool:
        """Validate Bluesky collector configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        if not self.enabled:
            return True
        
        # Check API credentials
        handle = self.config.get("handle") or os.getenv("BLUESKY_HANDLE")
        password = self.config.get("password") or os.getenv("BLUESKY_PASSWORD")
        
        if not handle or not password:
            print("Missing Bluesky credentials")
            return False
        
        # Validate max_posts
        max_posts = self.config.get("max_posts", 1000)
        if not isinstance(max_posts, int) or max_posts <= 0:
            print("Invalid max_posts configuration")
            return False
        
        return True
    
    def get_platform_name(self) -> str:
        """Get platform name.
        
        Returns:
            Platform name
        """
        return "bluesky"
    
    def test_connection(self) -> bool:
        """Test Bluesky API connection.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Try to get current user info
            self.client.app.bsky.actor.get_profile(actor="self")
            return True
        except Exception as e:
            print(f"Bluesky API connection failed: {e}")
            return False
