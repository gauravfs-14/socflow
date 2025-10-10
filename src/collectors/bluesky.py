"""Bluesky data collector."""

import asyncio
import json
import os
import websockets
from typing import Any, Dict, List, Optional

from atproto import Client, models

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
    
    def collect_continuous(self, keywords: Optional[List[str]] = None, hashtags: Optional[List[str]] = None, **kwargs) -> List[BlueskyPost]:
        """Collect data continuously from Bluesky using search and hashtag methods.
        
        Args:
            keywords: Optional keywords to search for
            hashtags: Optional hashtags to search for
            **kwargs: Additional collection parameters
            
        Returns:
            List of collected Bluesky posts
        """
        if not self.is_enabled():
            return []
        
        posts = []
        batch_size = 30  # Bluesky API limit is 100, so 30 is safe
        
        try:
            # Get keywords and hashtags from config if not provided
            if not keywords:
                keywords = self.config.get("keywords", [])
            if not hashtags:
                hashtags = self.config.get("hashtags", [])
            
            # Search by keywords
            if keywords:
                for keyword in keywords[:5]:  # Limit to first 5 keywords for performance
                    try:
                        search_posts = self._search_by_keyword(keyword, batch_size)
                        posts.extend(search_posts)
                        print(f"🔍 Searched '{keyword}' - found {len(search_posts)} posts")
                    except Exception as e:
                        print(f"Error searching '{keyword}': {e}")
                        continue
            
            # Search by hashtags
            if hashtags:
                for hashtag in hashtags[:5]:  # Limit to first 5 hashtags for performance
                    try:
                        hashtag_posts = self._search_by_hashtag(hashtag, batch_size)
                        posts.extend(hashtag_posts)
                        print(f"🏷️ Searched '{hashtag}' - found {len(hashtag_posts)} posts")
                    except Exception as e:
                        print(f"Error searching '{hashtag}': {e}")
                        continue
            
            # If no keywords or hashtags, use public feed
            if not keywords and not hashtags:
                public_posts = self._get_public_feed(batch_size)
                posts.extend(public_posts)
                print(f"🌐 Public feed - found {len(public_posts)} posts")
        
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
            # Limit to 30 posts per search (Bluesky API limit is 100)
            limit = min(max_posts, 30)
            search_results = self.client.app.bsky.feed.search_posts(
                params={"q": keyword, "limit": limit}
            )
            
            for post_data in search_results.posts:
                try:
                    post = BlueskyPost.from_atproto_record(post_data)
                    posts.append(post)
                except Exception as e:
                    print(f"Error processing post: {e}")
                    continue
        
        except Exception as e:
            print(f"Error searching for keyword '{keyword}': {e}")
        
        return posts
    
    def _search_by_hashtag(self, hashtag: str, max_posts: int) -> List[BlueskyPost]:
        """Search posts by hashtag.
        
        Args:
            hashtag: Hashtag to search for (with or without #)
            max_posts: Maximum number of posts to collect
            
        Returns:
            List of Bluesky posts
        """
        posts = []
        
        try:
            # Ensure hashtag starts with #
            if not hashtag.startswith('#'):
                hashtag = f"#{hashtag}"
            
            # Search for posts containing the hashtag
            # Limit to 30 posts per search (Bluesky API limit is 100)
            limit = min(max_posts, 30)
            search_results = self.client.app.bsky.feed.search_posts(
                params={"q": hashtag, "limit": limit}
            )
            
            for post_view in search_results.posts:
                try:
                    post = BlueskyPost.from_atproto_record(post_view)
                    posts.append(post)
                except Exception as e:
                    print(f"Error processing hashtag post: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error searching hashtag '{hashtag}': {e}")
        
        return posts
    
    def _get_public_feed(self, max_posts: int) -> List[BlueskyPost]:
        """Get posts from public feed (not personal timeline).
        
        Args:
            max_posts: Maximum number of posts to collect
            
        Returns:
            List of Bluesky posts
        """
        posts = []
        
        try:
            # Get public feed using the get_timeline API
            # This should give us public posts, not personal timeline
            public_feed = self.client.app.bsky.feed.get_timeline()
            
            for feed_item in public_feed.feed[:max_posts]:
                try:
                    if hasattr(feed_item, 'post') and feed_item.post:
                        post = BlueskyPost.from_atproto_record(feed_item.post)
                        posts.append(post)
                except Exception as e:
                    print(f"Error processing public feed post: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error getting public feed: {e}")
        
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
            # Get timeline (limit parameter not supported in this API version)
            timeline = self.client.app.bsky.feed.get_timeline()
            
            for feed_item in timeline.feed:
                try:
                    if hasattr(feed_item, 'post') and feed_item.post:
                        post = BlueskyPost.from_atproto_record(feed_item.post)
                        posts.append(post)
                        # Stop if we have enough posts
                        if len(posts) >= max_posts:
                            break
                except Exception as e:
                    print(f"Error processing timeline post: {e}")
                    continue
        
        except Exception as e:
            print(f"Error getting timeline: {e}")
        
        return posts
    
    def _get_firehose_posts_websocket(self) -> List[BlueskyPost]:
        """Get posts from Bluesky WebSocket firehose for real-time streaming.
        
        Returns:
            List of firehose posts
        """
        posts = []
        
        try:
            # Use asyncio to run the WebSocket connection
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run the WebSocket connection for a short time to collect posts
            posts = loop.run_until_complete(self._websocket_firehose_collector())
            loop.close()
            
        except Exception as e:
            print(f"Error with WebSocket firehose: {e}")
        
        return posts
    
    async def _websocket_firehose_collector(self) -> List[BlueskyPost]:
        """Async WebSocket firehose collector."""
        posts = []
        
        try:
            # Bluesky Jetstream WebSocket endpoint
            uri = "wss://jetstream2.us-west.bsky.network/subscribe?wantedCollections=app.bsky.feed.post"
            async with websockets.connect(uri) as websocket:
                # Collect posts for a limited time to prevent hanging
                timeout = 15  # seconds
                start_time = asyncio.get_event_loop().time()
                message_count = 0
                
                while (asyncio.get_event_loop().time() - start_time) < timeout:
                    try:
                        # Wait for message with timeout
                        message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        message_count += 1
                        
                        # Parse the JSON message
                        data = json.loads(message)
                        
                        
                        # Extract post data from the firehose message
                        # The structure is: data.commit.collection == 'app.bsky.feed.post'
                        if (data.get('kind') == 'commit' and 
                            'commit' in data and 
                            data['commit'].get('collection') == 'app.bsky.feed.post'):
                            
                            try:
                                commit = data['commit']
                                
                                # Create a mock post view for the BlueskyPost model
                                post_data = {
                                    'uri': commit.get('uri', ''),
                                    'cid': commit.get('cid', ''),
                                    'record': commit.get('record', {}),
                                    'author': data.get('author', {}),
                                    'replyCount': 0,
                                    'repostCount': 0,
                                    'likeCount': 0,
                                    'indexedAt': data.get('time_us', ''),
                                }
                                
                                # Create BlueskyPost from firehose data
                                post = BlueskyPost.from_atproto_record(post_data)
                                posts.append(post)
                                
                                # Limit posts to prevent memory issues
                                if len(posts) >= 50:
                                    break
                                    
                            except Exception as e:
                                print(f"Error processing firehose post: {e}")
                                continue
                    except asyncio.TimeoutError:
                        # Timeout waiting for message, continue
                        continue
                    except Exception as e:
                        print(f"Error receiving message: {e}")
                        continue
                
                                
        except asyncio.TimeoutError:
            print("WebSocket timeout - collected available posts")
        except websockets.ConnectionClosed:
            print("WebSocket connection closed")
        except Exception as e:
            print(f"WebSocket error: {e}")
        
        return posts
    
    def _get_firehose_posts(self, max_posts: int) -> List[BlueskyPost]:
        """Get posts from Bluesky firehose (public feed).
        
        Args:
            max_posts: Maximum number of posts to collect
            
        Returns:
            List of firehose posts
        """
        posts = []
        
        try:
            # Get public feed (firehose) - use standard timeline
            public_feed = self.client.app.bsky.feed.get_timeline()
            
            for feed_item in public_feed.feed:
                try:
                    if hasattr(feed_item, 'post') and feed_item.post:
                        post = BlueskyPost.from_atproto_record(feed_item.post)
                        posts.append(post)
                        # Stop if we have enough posts
                        if len(posts) >= max_posts:
                            break
                except Exception as e:
                    print(f"Error processing firehose post: {e}")
                    continue
        
        except Exception as e:
            print(f"Error getting firehose: {e}")
        
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
            
            for feed_item in user_posts.feed:
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
