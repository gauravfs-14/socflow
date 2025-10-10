"""Reddit data collector."""

import os
from typing import Any, Dict, List, Optional

import praw
from tqdm import tqdm

from ..models.reddit import RedditPost
from .base import BaseCollector


class RedditCollector(BaseCollector):
    """Reddit data collector."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Reddit collector.
        
        Args:
            config: Reddit collector configuration
        """
        super().__init__(config)
        self.reddit = None
        self._setup_reddit_client()
    
    def _setup_reddit_client(self) -> None:
        """Setup Reddit API client."""
        client_id = self.config.get("client_id") or os.getenv("REDDIT_CLIENT_ID")
        client_secret = self.config.get("client_secret") or os.getenv("REDDIT_CLIENT_SECRET")
        user_agent = self.config.get("user_agent", "SocFlow/1.0")
        
        if not client_id or not client_secret:
            raise ValueError("Reddit API credentials not found. Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET environment variables.")
        
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
    
    def collect(self, subreddits: Optional[List[str]] = None, keywords: Optional[List[str]] = None, **kwargs) -> List[RedditPost]:
        """Collect data from Reddit.
        
        Args:
            subreddits: List of subreddits to collect from. If None, uses config default.
            keywords: Optional keywords to search for. If provided, uses search API.
            **kwargs: Additional collection parameters
            
        Returns:
            List of collected Reddit posts
        """
        if not self.is_enabled():
            return []
        
        if not self.validate_config():
            raise ValueError("Invalid Reddit collector configuration")
        
        if subreddits is None:
            subreddits = self.config.get("subreddits", ["all"])
        
        posts = []
        max_posts = self.config.get("max_posts_per_subreddit", 1000)
        
        try:
            if keywords:
                # Use search API when keywords provided
                for keyword in keywords:
                    keyword_posts = self._search_by_keyword(keyword, max_posts // len(keywords))
                    posts.extend(keyword_posts)
            else:
                # Use subreddit feeds when no keywords
                sort_by = self.config.get("sort_by", "hot")
                time_filter = self.config.get("time_filter", "day")
                
                for subreddit_name in subreddits:
                    try:
                        subreddit_posts = self._collect_from_subreddit(
                            subreddit_name, max_posts, sort_by, time_filter
                        )
                        posts.extend(subreddit_posts)
                    except Exception as e:
                        print(f"Error collecting from r/{subreddit_name}: {e}")
                        continue
        except Exception as e:
            print(f"Error in Reddit collection: {e}")
        
        return posts
    
    def collect_continuous(self, subreddits: Optional[List[str]] = None, keywords: Optional[List[str]] = None, **kwargs) -> List[RedditPost]:
        """Collect data continuously from Reddit.
        
        Args:
            subreddits: List of subreddits to collect from. If None, uses config default.
            keywords: Optional keywords to search for. If provided, uses search API.
            **kwargs: Additional collection parameters
            
        Returns:
            List of collected Reddit posts
        """
        if not self.is_enabled():
            return []
        
        if subreddits is None:
            subreddits = self.config.get("subreddits", ["all"])
        
        posts = []
        batch_size = 10
        
        try:
            if keywords:
                # Use search API when keywords provided
                for keyword in keywords:
                    keyword_posts = self._search_by_keyword(keyword, batch_size)
                    posts.extend(keyword_posts)
            else:
                # Use subreddit feeds when no keywords
                sort_by = self.config.get("sort_by", "hot")
                time_filter = self.config.get("time_filter", "day")
                
                for subreddit_name in subreddits:
                    try:
                        subreddit_posts = self._collect_from_subreddit(
                            subreddit_name, batch_size, sort_by, time_filter
                        )
                        posts.extend(subreddit_posts)
                    except Exception as e:
                        print(f"Error collecting from r/{subreddit_name}: {e}")
                        continue
        except Exception as e:
            print(f"Error in Reddit collection: {e}")
        
        return posts
    
    def _collect_from_subreddit(
        self, 
        subreddit_name: str, 
        max_posts: int, 
        sort_by: str, 
        time_filter: str
    ) -> List[RedditPost]:
        """Collect posts from a specific subreddit.
        
        Args:
            subreddit_name: Name of the subreddit
            max_posts: Maximum number of posts to collect
            sort_by: How to sort posts (hot, new, top, rising)
            time_filter: Time filter for top posts
            
        Returns:
            List of posts from the subreddit
        """
        subreddit = self.reddit.subreddit(subreddit_name)
        posts = []
        
        # Get posts based on sort method
        if sort_by == "hot":
            submissions = subreddit.hot(limit=max_posts)
        elif sort_by == "new":
            submissions = subreddit.new(limit=max_posts)
        elif sort_by == "top":
            submissions = subreddit.top(limit=max_posts, time_filter=time_filter)
        elif sort_by == "rising":
            submissions = subreddit.rising(limit=max_posts)
        else:
            raise ValueError(f"Invalid sort method: {sort_by}")
        
        # Convert submissions to RedditPost objects
        for submission in tqdm(submissions, desc=f"Collecting from r/{subreddit_name}"):
            try:
                post = RedditPost.from_praw_submission(submission)
                posts.append(post)
            except Exception as e:
                print(f"Error processing submission {submission.id}: {e}")
                continue
        
        return posts
    
    def _search_by_keyword(self, keyword: str, max_posts: int) -> List[RedditPost]:
        """Search Reddit posts by keyword.
        
        Args:
            keyword: Keyword to search for
            max_posts: Maximum number of posts to collect
            
        Returns:
            List of posts matching the keyword
        """
        posts = []
        
        try:
            # Search across all of Reddit for the keyword
            search_results = self.reddit.subreddit("all").search(keyword, limit=max_posts, sort="relevance", time_filter="week")
            
            for submission in tqdm(search_results, desc=f"Searching Reddit for '{keyword}'"):
                try:
                    post = RedditPost.from_praw_submission(submission)
                    posts.append(post)
                except Exception as e:
                    print(f"Error processing submission {submission.id}: {e}")
                    continue
        except Exception as e:
            print(f"Error searching Reddit for '{keyword}': {e}")
        
        return posts
    
    def collect_comments(self, post_id: str, max_comments: int = 100) -> List[RedditPost]:
        """Collect comments from a specific post.
        
        Args:
            post_id: Reddit post ID
            max_comments: Maximum number of comments to collect
            
        Returns:
            List of comment posts
        """
        if not self.is_enabled():
            return []
        
        try:
            submission = self.reddit.submission(id=post_id)
            comments = []
            
            # Collect top-level comments
            submission.comments.replace_more(limit=0)
            for comment in submission.comments.list()[:max_comments]:
                try:
                    comment_post = RedditPost.from_praw_comment(comment)
                    comments.append(comment_post)
                except Exception as e:
                    print(f"Error processing comment {comment.id}: {e}")
                    continue
            
            return comments
        except Exception as e:
            print(f"Error collecting comments from post {post_id}: {e}")
            return []
    
    def validate_config(self) -> bool:
        """Validate Reddit collector configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        if not self.enabled:
            return True
        
        # Check required fields
        required_fields = ["subreddits"]
        for field in required_fields:
            if field not in self.config:
                print(f"Missing required field: {field}")
                return False
        
        # Check API credentials
        client_id = self.config.get("client_id") or os.getenv("REDDIT_CLIENT_ID")
        client_secret = self.config.get("client_secret") or os.getenv("REDDIT_CLIENT_SECRET")
        
        if not client_id or not client_secret:
            print("Missing Reddit API credentials")
            return False
        
        # Validate subreddits
        subreddits = self.config.get("subreddits", [])
        if not isinstance(subreddits, list) or len(subreddits) == 0:
            print("Invalid subreddits configuration")
            return False
        
        return True
    
    def get_platform_name(self) -> str:
        """Get platform name.
        
        Returns:
            Platform name
        """
        return "reddit"
    
    def test_connection(self) -> bool:
        """Test Reddit API connection.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Try to access Reddit API
            self.reddit.user.me()
            return True
        except Exception as e:
            print(f"Reddit API connection failed: {e}")
            return False
