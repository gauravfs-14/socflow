"""Mastodon data collector."""

import os
from typing import Any, Dict, List, Optional

from mastodon import Mastodon

from ..models.mastodon import MastodonPost
from .base import BaseCollector


class MastodonCollector(BaseCollector):
    """Mastodon data collector."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Mastodon collector.
        
        Args:
            config: Mastodon collector configuration
        """
        super().__init__(config)
        self.clients = {}
        self._setup_clients()
    
    def _setup_clients(self) -> None:
        """Setup Mastodon clients for each instance."""
        instances = self.config.get("instances", ["https://mastodon.social"])
        access_token = self.config.get("access_token") or os.getenv("MASTODON_ACCESS_TOKEN")
        
        if not access_token:
            raise ValueError("Mastodon access token not found. Set MASTODON_ACCESS_TOKEN environment variable.")
        
        for instance in instances:
            try:
                client = Mastodon(
                    access_token=access_token,
                    api_base_url=instance
                )
                # Test the connection
                client.account_verify_credentials()
                self.clients[instance] = client
            except Exception as e:
                print(f"Failed to connect to {instance}: {e}")
                continue
    
    def collect(self, instances: Optional[List[str]] = None, hashtags: Optional[List[str]] = None, **kwargs) -> List[MastodonPost]:
        """Collect data from Mastodon.
        
        Args:
            instances: List of instances to collect from. If None, uses config default.
            hashtags: List of hashtags to search for. If None, uses config default.
            **kwargs: Additional collection parameters
            
        Returns:
            List of collected Mastodon posts
        """
        if not self.is_enabled():
            return []
        
        if not self.validate_config():
            raise ValueError("Invalid Mastodon collector configuration")
        
        if instances is None:
            instances = self.config.get("instances", ["https://mastodon.social"])
        
        if hashtags is None:
            hashtags = self.config.get("hashtags", [])
        
        posts = []
        max_posts_per_instance = self.config.get("max_posts_per_instance", 1000)
        
        for instance in instances:
            if instance not in self.clients:
                print(f"No client available for {instance}")
                continue
            
            try:
                instance_posts = self._collect_from_instance(
                    instance, max_posts_per_instance, hashtags
                )
                posts.extend(instance_posts)
            except Exception as e:
                print(f"Error collecting from {instance}: {e}")
                continue
        
        return posts
    
    def collect_continuous(self, instances: Optional[List[str]] = None, hashtags: Optional[List[str]] = None, **kwargs) -> List[MastodonPost]:
        """Collect data continuously from Mastodon.
        
        Args:
            instances: List of instances to collect from. If None, uses config default.
            hashtags: Optional hashtags to filter posts by
            **kwargs: Additional collection parameters
            
        Returns:
            List of collected Mastodon posts
        """
        if not self.is_enabled():
            return []
        
        if instances is None:
            instances = self.config.get("instances", ["https://mastodon.social"])
        
        posts = []
        batch_size = 10
        
        for instance in instances:
            if instance not in self.clients:
                continue
            
            try:
                instance_posts = self._collect_from_instance(
                    instance, batch_size, hashtags or []
                )
                posts.extend(instance_posts)
            except Exception as e:
                print(f"Error collecting from {instance}: {e}")
                continue
        
        return posts
    
    def _collect_from_instance(
        self, 
        instance: str, 
        max_posts: int, 
        hashtags: List[str]
    ) -> List[MastodonPost]:
        """Collect posts from a specific instance.
        
        Args:
            instance: Mastodon instance URL
            max_posts: Maximum number of posts to collect
            hashtags: List of hashtags to search for
            
        Returns:
            List of posts from the instance
        """
        client = self.clients[instance]
        posts = []
        
        try:
            if hashtags:
                # Search by hashtags
                for hashtag in hashtags:
                    hashtag_posts = self._search_by_hashtag(client, hashtag, max_posts // len(hashtags))
                    posts.extend(hashtag_posts)
            else:
                # Get public timeline
                timeline_posts = self._get_public_timeline(client, max_posts)
                posts.extend(timeline_posts)
        
        except Exception as e:
            print(f"Error collecting from {instance}: {e}")
        
        return posts
    
    def _search_by_hashtag(self, client: Mastodon, hashtag: str, max_posts: int) -> List[MastodonPost]:
        """Search posts by hashtag.
        
        Args:
            client: Mastodon client
            hashtag: Hashtag to search for
            max_posts: Maximum number of posts to collect
            
        Returns:
            List of posts with the hashtag
        """
        posts = []
        
        try:
            # Search for posts with the hashtag
            search_results = client.timeline_hashtag(hashtag, limit=max_posts)
            
            for status in search_results:
                try:
                    # Extract instance from client's api_base_url
                    instance = client.api_base_url.replace('https://', '').replace('http://', '')
                    post = MastodonPost.from_mastodon_status(status, instance)
                    posts.append(post)
                    # print(f"✅ Successfully created post: {post.text[:50]}...")
                except Exception as e:
                    print(f"❌ Error processing post: {e}")
                    print(f"Status type: {type(status)}")
                    print(f"Status keys: {list(status.keys()) if isinstance(status, dict) else 'Not a dict'}")
                    continue
        
        except Exception as e:
            print(f"Error searching for hashtag #{hashtag}: {e}")
        
        return posts
    
    def _get_public_timeline(self, client: Mastodon, max_posts: int) -> List[MastodonPost]:
        """Get posts from public timeline.
        
        Args:
            client: Mastodon client
            max_posts: Maximum number of posts to collect
            
        Returns:
            List of public timeline posts
        """
        posts = []
        
        try:
            # Get public timeline
            timeline = client.timeline_public(limit=max_posts)
            
            for status in timeline:
                try:
                    # Extract instance from client's api_base_url
                    instance = client.api_base_url.replace('https://', '').replace('http://', '')
                    post = MastodonPost.from_mastodon_status(status, instance)
                    posts.append(post)
                except Exception as e:
                    print(f"Error processing timeline post: {e}")
                    continue
        
        except Exception as e:
            print(f"Error getting public timeline: {e}")
        
        return posts
    
    def get_user_posts(self, handle: str, max_posts: int = 100) -> List[MastodonPost]:
        """Get posts from a specific user.
        
        Args:
            handle: User handle (e.g., @user@instance.com)
            max_posts: Maximum number of posts to collect
            
        Returns:
            List of user posts
        """
        if not self.is_enabled():
            return []
        
        posts = []
        
        try:
            # Parse handle to get username and instance
            if '@' in handle:
                username, instance = handle.split('@', 1)
                if instance not in self.clients:
                    print(f"No client available for {instance}")
                    return []
                
                client = self.clients[instance]
                
                # Get user's posts
                user_posts = client.account_statuses(
                    account_id=username,
                    limit=max_posts
                )
                
                for status in user_posts:
                    try:
                        post = MastodonPost.from_mastodon_status(status, instance)
                        posts.append(post)
                    except Exception as e:
                        print(f"Error processing user post: {e}")
                        continue
            else:
                print(f"Invalid handle format: {handle}")
        
        except Exception as e:
            print(f"Error getting posts from user {handle}: {e}")
        
        return posts
    
    def validate_config(self) -> bool:
        """Validate Mastodon collector configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        if not self.enabled:
            return True
        
        # Check required fields
        required_fields = ["instances"]
        for field in required_fields:
            if field not in self.config:
                print(f"Missing required field: {field}")
                return False
        
        # Check API credentials
        access_token = self.config.get("access_token") or os.getenv("MASTODON_ACCESS_TOKEN")
        if not access_token:
            print("Missing Mastodon access token")
            return False
        
        # Validate instances
        instances = self.config.get("instances", [])
        if not isinstance(instances, list) or len(instances) == 0:
            print("Invalid instances configuration")
            return False
        
        # Validate max_posts_per_instance
        max_posts = self.config.get("max_posts_per_instance", 1000)
        if not isinstance(max_posts, int) or max_posts <= 0:
            print("Invalid max_posts_per_instance configuration")
            return False
        
        return True
    
    def get_platform_name(self) -> str:
        """Get platform name.
        
        Returns:
            Platform name
        """
        return "mastodon"
    
    def test_connection(self) -> bool:
        """Test Mastodon API connection.
        
        Returns:
            True if connection is successful, False otherwise
        """
        if not self.clients:
            return False
        
        try:
            # Test the first available client
            client = next(iter(self.clients.values()))
            client.account_verify_credentials()
            return True
        except Exception as e:
            print(f"Mastodon API connection failed: {e}")
            return False
