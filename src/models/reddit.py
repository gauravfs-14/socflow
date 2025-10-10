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
    """Reddit post model - simplified."""
    
    platform: str = Field(default="reddit", description="Platform identifier")
    subreddit: str = Field(description="Subreddit name")
    title: str = Field(description="Post title")
    is_nsfw: bool = Field(default=False, description="Whether this is NSFW")
    metrics: RedditMetrics = Field(default_factory=RedditMetrics)
    
    @classmethod
    def from_praw_submission(cls, submission: Any) -> "RedditPost":
        """Create RedditPost from PRAW submission object - simplified."""
        return cls(
            platform="reddit",
            object_id=submission.id,
            author_handle=submission.author.name if submission.author else "[deleted]",
            text=submission.selftext or submission.title,
            created_at=datetime.fromtimestamp(submission.created_utc),
            tags=[],  # No tags for Reddit
            subreddit=submission.subreddit.display_name,
            title=submission.title,
            is_nsfw=submission.over_18,
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
        """Create RedditPost from PRAW comment object - simplified."""
        return cls(
            platform="reddit",
            object_id=comment.id,
            author_handle=comment.author.name if comment.author else "[deleted]",
            text=comment.body,
            created_at=datetime.fromtimestamp(comment.created_utc),
            tags=[],  # No tags for Reddit
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
