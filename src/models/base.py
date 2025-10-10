"""Base data models for SocFlow."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class Metrics(BaseModel):
    """Social media metrics."""
    
    likes: int = Field(default=0, description="Number of likes")
    shares: int = Field(default=0, description="Number of shares/retweets")
    comments: int = Field(default=0, description="Number of comments/replies")
    upvotes: int = Field(default=0, description="Number of upvotes")
    downvotes: int = Field(default=0, description="Number of downvotes")
    views: Optional[int] = None
    
    class Config:
        extra = "allow"  # Allow additional metrics from different platforms


class BasePost(BaseModel):
    """Base post model for all platforms - simplified."""
    
    platform: str = Field(description="Source platform (reddit, bluesky, mastodon)")
    object_id: str = Field(description="Unique ID per platform")
    author_handle: str = Field(description="Username or handle")
    text: str = Field(description="Post or comment text")
    created_at: datetime = Field(description="Timestamp")
    tags: List[str] = Field(default_factory=list, description="Hashtags (only for Bluesky)")
    metrics: Metrics = Field(default_factory=Metrics, description="Social media metrics")
    url: Optional[str] = None
    parent_id: Optional[str] = None
    is_comment: bool = Field(default=False, description="Whether this is a comment")
    raw_data: Optional[Union[Dict[str, Any], str]] = None
    
    class Config:
        extra = "allow"  # Allow platform-specific fields
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return self.dict()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BasePost":
        """Create from dictionary."""
        return cls(**data)
