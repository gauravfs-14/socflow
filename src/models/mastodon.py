"""Mastodon-specific data models."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from .base import BasePost, Metrics


class MastodonMetrics(BaseModel):
    """Mastodon-specific metrics."""
    
    favourites: int = Field(default=0, description="Number of favourites")
    reblogs: int = Field(default=0, description="Number of reblogs")
    replies: int = Field(default=0, description="Number of replies")


class MastodonPost(BaseModel):
    """Mastodon post model."""
    
    # Essential fields only
    platform: str = Field(default="mastodon", description="Platform identifier")
    object_id: str = Field(description="Unique ID per platform")
    author_handle: str = Field(description="Username or handle")
    text: str = Field(description="Post or comment text")
    created_at: datetime = Field(description="Timestamp")
    tags: List[str] = Field(default_factory=list, description="Hashtags or communities")
    url: Optional[str] = None
    parent_id: Optional[str] = None
    is_comment: bool = Field(default=False, description="Whether this is a comment")
    raw_data: Optional[Union[Dict[str, Any], str]] = None
    
    # Mastodon-specific fields
    instance: str = Field(description="Mastodon instance domain")
    handle: str = Field(description="User handle (e.g., @user@instance.com)")
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_reply: bool = Field(default=False, description="Whether this is a reply")
    is_reblog: bool = Field(default=False, description="Whether this is a reblog")
    is_sensitive: bool = Field(default=False, description="Whether this is marked as sensitive")
    is_boosted: bool = Field(default=False, description="Whether this is boosted")
    reply_to: Optional[str] = None
    reblog_of: Optional[str] = None
    language: Optional[str] = None
    spoiler_text: Optional[str] = None
    images: List[str] = Field(default_factory=list, description="Image URLs")
    links: List[str] = Field(default_factory=list, description="Link URLs")
    metrics: MastodonMetrics = Field(default_factory=MastodonMetrics)
    
    class Config:
        extra = "allow"  # Allow platform-specific fields
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @classmethod
    def from_mastodon_status(cls, status: Dict[str, Any], instance: str) -> "MastodonPost":
        """Create MastodonPost from Mastodon status object."""
        # Extract basic post information
        # Handle MaybeSnowflakeIdType properly - access attributes directly
        raw_id = getattr(status, 'id', "")
        if hasattr(raw_id, '__str__'):
            post_id = str(raw_id)
        else:
            post_id = str(raw_id) if raw_id else ""
        
        text = getattr(status, 'content', "")
        created_at = getattr(status, 'created_at', "")
        
        # Parse timestamp - handle both string and datetime objects
        if isinstance(created_at, datetime):
            created_at_dt = created_at
        else:
            try:
                created_at_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                created_at_dt = datetime.now()
        
        # Extract author information
        account = getattr(status, 'account', {})
        handle = getattr(account, 'acct', "") if account else ""
        display_name = getattr(account, 'display_name', None) if account else None
        avatar_url = getattr(account, 'avatar', None) if account else None
        
        # Extract media
        media_attachments = getattr(status, 'media_attachments', [])
        images = [getattr(media, 'url', "") for media in media_attachments if getattr(media, 'type', '') == "image"]
        
        # Extract links from text (basic implementation)
        links = []
        if "http" in text:
            import re
            url_pattern = r'https?://[^\s<>"]+'
            links = re.findall(url_pattern, text)
        
        # Extract hashtags
        tags = []
        status_tags = getattr(status, 'tags', [])
        if status_tags:
            tags = [getattr(tag, 'name', "") for tag in status_tags]
        
        try:
            # Create a minimal post first
            post = cls(
                platform="mastodon",
                object_id=post_id,
                author_handle=handle,
                text=text,
                created_at=created_at_dt,
                tags=tags,
                instance=instance,
                handle=handle,
                display_name=display_name,
                avatar_url=avatar_url,
                is_reply=bool(getattr(status, 'in_reply_to_id', None)),
                is_reblog=bool(getattr(status, 'reblog', None)),
                is_sensitive=getattr(status, 'sensitive', False),
                is_boosted=bool(getattr(status, 'reblog', None)),
                reply_to=str(getattr(status, 'in_reply_to_id', None)) if getattr(status, 'in_reply_to_id', None) else None,
                reblog_of=str(getattr(getattr(status, 'reblog', {}), 'id', "")) if getattr(status, 'reblog', None) else None,
                language=getattr(status, 'language', None),
                spoiler_text=getattr(status, 'spoiler_text', None),
                images=images,
                links=links,
                url=getattr(status, 'url', ""),
                metrics=MastodonMetrics(
                    favourites=0,  # Simplified for now
                    reblogs=0,
                    replies=0,
                ),
                raw_data=status
            )
            return post
        except Exception as e:
            print(f"Error creating MastodonPost: {e}")
            print(f"Status data keys: {list(status.keys()) if isinstance(status, dict) else 'Not a dict'}")
            print(f"Post ID: {post_id} (type: {type(post_id)})")
            print(f"Text: {text[:50]}... (type: {type(text)})")
            print(f"Handle: {handle} (type: {type(handle)})")
            raise
