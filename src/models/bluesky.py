"""Bluesky-specific data models."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field

from .base import BasePost, Metrics


class BlueskyMetrics(Metrics):
    """Bluesky-specific metrics."""
    
    likes: int = Field(default=0, description="Number of likes")
    reposts: int = Field(default=0, description="Number of reposts")
    replies: int = Field(default=0, description="Number of replies")


class BlueskyPost(BasePost):
    """Bluesky post model - simplified."""
    
    platform: str = Field(default="bluesky", description="Platform identifier")
    handle: str = Field(description="User handle (e.g., @user.bsky.app)")
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_reply: bool = Field(default=False, description="Whether this is a reply")
    is_repost: bool = Field(default=False, description="Whether this is a repost")
    reply_to: Optional[str] = None
    repost_of: Optional[str] = None
    metrics: BlueskyMetrics = Field(default_factory=BlueskyMetrics)
    
    @classmethod
    def from_atproto_record(cls, post_view: Any) -> "BlueskyPost":
        """Create BlueskyPost from AT Protocol post view."""
        try:
            # Extract basic post information from post view
            post_id = getattr(post_view, 'uri', '').split("/")[-1] if hasattr(post_view, 'uri') else ""
            text = getattr(post_view.record, 'text', '') if hasattr(post_view, 'record') and hasattr(post_view.record, 'text') else ""
            created_at = getattr(post_view.record, 'created_at', '') if hasattr(post_view, 'record') and hasattr(post_view.record, 'created_at') else ""
            
            # Parse timestamp
            try:
                created_at_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                created_at_dt = datetime.now()
            
            # Extract author information from post view
            author = getattr(post_view, 'author', None) if hasattr(post_view, 'author') else None
            handle = getattr(author, 'handle', '') if author and hasattr(author, 'handle') else ""
            display_name = getattr(author, 'displayName', None) if author and hasattr(author, 'displayName') else None
            avatar_url = getattr(author, 'avatar', None) if author and hasattr(author, 'avatar') else None
            
            # For now, use default values for metrics since they're not easily accessible
            return cls(
                platform="bluesky",
                object_id=post_id,
                author_handle=handle,
                text=text,
                created_at=created_at_dt,
                tags=[],  # Tags not directly available in basic API response
                handle=handle,
                display_name=display_name,
                avatar_url=avatar_url,
                is_reply=False,  # Simplified for now
                is_repost=False,  # Simplified for now
                reply_to=None,
                repost_of=None,
                url=f"https://bsky.app/profile/{handle}/post/{post_id}",
                metrics=BlueskyMetrics(
                    likes=0,  # Default values
                    reposts=0,
                    replies=0,
                ),
                raw_data=str(post_view)  # Convert to string for storage
            )
        except Exception as e:
            # Return a minimal post if parsing fails
            return cls(
                platform="bluesky",
                object_id="unknown",
                author_handle="unknown",
                text="",
                created_at=datetime.now(),
                tags=[],
                handle="unknown",
                display_name=None,
                avatar_url=None,
                is_reply=False,
                is_repost=False,
                reply_to=None,
                repost_of=None,
                url="",
                metrics=BlueskyMetrics(),
                raw_data=str(post_view)
            )
