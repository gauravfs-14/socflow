"""Reddit-specific data models."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field

from .base import BasePost, Metrics


class RedditMetrics(Metrics):
    """Reddit-specific metrics."""
    
    upvotes: int = Field(default=0, description="Number of upvotes")
    downvotes: int = Field(default=0, description="Number of downvotes")
    score: int = Field(default=0, description="Net score (upvotes - downvotes)")
    gilded: int = Field(default=0, description="Number of gold awards")


class RedditPost(BasePost):
    """Reddit post model."""
    
    platform: str = Field(default="reddit", description="Platform identifier")
    subreddit: str = Field(description="Subreddit name")
    title: str = Field(description="Post title")
    flair: Optional[str] = None
    is_self: bool = Field(default=True, description="Whether this is a self post")
    is_nsfw: bool = Field(default=False, description="Whether this is NSFW")
    is_locked: bool = Field(default=False, description="Whether this is locked")
    is_archived: bool = Field(default=False, description="Whether this is archived")
    is_stickied: bool = Field(default=False, description="Whether this is stickied")
    link_url: Optional[str] = None
    domain: Optional[str] = None
    metrics: RedditMetrics = Field(default_factory=RedditMetrics)
    
    @classmethod
    def from_praw_submission(cls, submission: Any) -> "RedditPost":
        """Create RedditPost from PRAW submission object."""
        return cls(
            platform="reddit",
            object_id=submission.id,
            author_handle=submission.author.name if submission.author else "[deleted]",
            text=submission.selftext or submission.title,
            created_at=datetime.fromtimestamp(submission.created_utc),
            tags=[submission.subreddit.display_name],
            subreddit=submission.subreddit.display_name,
            title=submission.title,
            flair=submission.link_flair_text,
            is_self=submission.is_self,
            is_nsfw=submission.over_18,
            is_locked=submission.locked,
            is_archived=submission.archived,
            is_stickied=submission.stickied,
            link_url=submission.url if not submission.is_self else None,
            domain=submission.domain if not submission.is_self else None,
            url=f"https://reddit.com{submission.permalink}",
            metrics=RedditMetrics(
                upvotes=submission.ups,
                downvotes=submission.downs,
                score=submission.score,
                comments=submission.num_comments,
                gilded=submission.gilded,
            ),
            raw_data={
                "submission_id": submission.id,
                "subreddit_id": submission.subreddit_id,
                "author_id": submission.author.id if submission.author else None,
                "created_utc": submission.created_utc,
                "edited": submission.edited,
                "distinguished": submission.distinguished,
                "mod_reports": submission.mod_reports,
                "user_reports": submission.user_reports,
            }
        )
    
    @classmethod
    def from_praw_comment(cls, comment: Any) -> "RedditPost":
        """Create RedditPost from PRAW comment object."""
        return cls(
            platform="reddit",
            object_id=comment.id,
            author_handle=comment.author.name if comment.author else "[deleted]",
            text=comment.body,
            created_at=datetime.fromtimestamp(comment.created_utc),
            tags=[comment.subreddit.display_name],
            subreddit=comment.subreddit.display_name,
            title="",  # Comments don't have titles
            is_comment=True,
            parent_id=comment.parent_id,
            url=f"https://reddit.com{comment.permalink}",
            metrics=RedditMetrics(
                upvotes=comment.ups,
                downvotes=comment.downs,
                score=comment.score,
                gilded=comment.gilded,
            ),
            raw_data={
                "comment_id": comment.id,
                "submission_id": comment.submission.id,
                "subreddit_id": comment.subreddit_id,
                "author_id": comment.author.id if comment.author else None,
                "created_utc": comment.created_utc,
                "edited": comment.edited,
                "distinguished": comment.distinguished,
                "mod_reports": comment.mod_reports,
                "user_reports": comment.user_reports,
            }
        )
