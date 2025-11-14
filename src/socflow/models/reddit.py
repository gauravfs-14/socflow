from datetime import datetime
from typing import Literal, Optional, Union, Any, List

from pydantic import BaseModel, Field, field_validator


class RedditPost(BaseModel):
    """Simplified Reddit post model for general use."""
    platform: Literal["reddit"] = "reddit"
    id: str
    content: str
    timestamp: datetime
    author: str
    full_content: str
    url: str
    source: str


class RedditComment(BaseModel):
    """PRAW Reddit Comment model."""
    id: str = Field(description="The ID of the comment")
    name: str = Field(description="Fullname of the comment (e.g., 't1_abc123')")
    author: Optional[str] = Field(
        default=None,
        description="Author username (None if deleted). Redditor object converted to string."
    )
    body: str = Field(description="The comment text")
    body_html: Optional[str] = Field(
        default=None,
        description="The comment text in HTML format"
    )
    created_utc: float = Field(description="Time the comment was created, represented in Unix Time")
    edited: Union[bool, float] = Field(
        default=False,
        description="Whether or not the comment has been edited. False if not edited, timestamp if edited."
    )
    score: int = Field(default=0, description="The number of upvotes for the comment")
    upvotes: Optional[int] = Field(default=None, description="Number of upvotes")
    downvotes: Optional[int] = Field(default=None, description="Number of downvotes")
    is_submitter: bool = Field(
        default=False,
        description="Whether or not the commenter is the submission's author"
    )
    distinguished: Optional[str] = Field(
        default=None,
        description="Whether or not the comment is distinguished. Values: 'moderator', 'admin', 'special', or None"
    )
    stickied: bool = Field(default=False, description="Whether or not the comment is stickied")
    parent_id: Optional[str] = Field(
        default=None,
        description="The ID of the parent comment or submission"
    )
    permalink: str = Field(description="A permalink for the comment")
    subreddit: str = Field(
        description="Subreddit name. Subreddit object converted to display_name string."
    )
    link_id: str = Field(description="The fullname of the submission this comment belongs to")
    depth: Optional[int] = Field(
        default=None,
        description="The depth of the comment in the comment tree"
    )

    @classmethod
    def from_praw_comment(cls, comment: Any) -> "RedditComment":
        """
        Create RedditComment from a PRAW Comment object.
        
        Args:
            comment: praw.reddit.models.Comment instance
            
        Returns:
            RedditComment model instance
        """
        # Extract author name (handle None for deleted users)
        author_name = None
        if hasattr(comment.author, 'name'):
            author_name = comment.author.name
        elif comment.author is not None:
            author_name = str(comment.author)
        
        # Extract subreddit name
        subreddit_name = comment.subreddit.display_name if hasattr(
            comment.subreddit, 'display_name'
        ) else str(comment.subreddit)
        
        return cls(
            id=comment.id,
            name=comment.name,
            author=author_name,
            body=comment.body,
            body_html=getattr(comment, 'body_html', None),
            created_utc=comment.created_utc,
            edited=comment.edited,
            score=comment.score,
            upvotes=getattr(comment, 'ups', None),
            downvotes=getattr(comment, 'downs', None),
            is_submitter=comment.is_submitter,
            distinguished=comment.distinguished,
            stickied=comment.stickied,
            parent_id=comment.parent_id,
            permalink=comment.permalink,
            subreddit=subreddit_name,
            link_id=comment.link_id,
            depth=getattr(comment, 'depth', None),
        )


class PollOption(BaseModel):
    """PRAW Poll Option model."""
    id: str = Field(description="The ID of the poll option")
    text: str = Field(description="The text of the poll option")
    vote_count: int = Field(default=0, description="The number of votes for this option")


class PollData(BaseModel):
    """PRAW Poll Data model."""
    options: List[PollOption] = Field(
        default_factory=list,
        description="List of poll options"
    )
    total_vote_count: int = Field(
        default=0,
        description="Total number of votes across all options"
    )
    user_selection: Optional[PollOption] = Field(
        default=None,
        description="The option selected by the current user, if any"
    )
    voting_end_timestamp: Optional[float] = Field(
        default=None,
        description="Unix timestamp when voting ends"
    )

    @classmethod
    def from_praw_poll_data(cls, poll_data: Any) -> "PollData":
        """
        Create PollData from a PRAW PollData object.
        
        Args:
            poll_data: praw.reddit.models.PollData instance
            
        Returns:
            PollData model instance
        """
        options = [
            PollOption(
                id=option.id,
                text=option.text,
                vote_count=option.vote_count
            )
            for option in poll_data.options
        ]
        
        user_selection = None
        if hasattr(poll_data, 'user_selection') and poll_data.user_selection:
            user_selection = PollOption(
                id=poll_data.user_selection.id,
                text=poll_data.user_selection.text,
                vote_count=poll_data.user_selection.vote_count
            )
        
        return cls(
            options=options,
            total_vote_count=poll_data.total_vote_count,
            user_selection=user_selection,
            voting_end_timestamp=getattr(poll_data, 'voting_end_timestamp', None),
        )


class RedditSubmission(BaseModel):
    """
    PRAW Reddit Submission model (PRAW 7.7.1 compatible).
    
    This model represents a Reddit submission (post) with all attributes
    from praw.reddit.models.Submission.
    """
    # Core identifiers
    id: str = Field(description="The ID of the submission")
    name: str = Field(description="Fullname of the submission (e.g., 't3_abc123')")
    
    # Author information
    author: Optional[str] = Field(
        default=None,
        description="Author username (None if deleted). Redditor object converted to string."
    )
    author_flair_text: Optional[str] = Field(
        default=None,
        description="The text content of the author's flair, or None if not flaired."
    )
    
    # Content
    title: str = Field(description="The title of the submission")
    selftext: str = Field(
        default="",
        description="The submission's selftext - an empty string if a link post."
    )
    url: str = Field(description="The URL the submission links to, or the permalink if a selfpost")
    permalink: str = Field(description="A permalink for the submission")
    
    # Metadata
    created_utc: float = Field(description="Time the submission was created, represented in Unix Time")
    edited: Union[bool, float] = Field(
        default=False,
        description="Whether or not the submission has been edited. False if not edited, timestamp if edited."
    )
    distinguished: Optional[str] = Field(
        default=None,
        description="Whether or not the submission is distinguished. Values: 'moderator', 'admin', 'special', or None"
    )
    
    # Subreddit information
    subreddit: str = Field(
        description="Subreddit name (e.g., 'python'). Subreddit object converted to display_name string."
    )
    
    # Interaction flags
    clicked: bool = Field(default=False, description="Whether or not the submission has been clicked by the client")
    saved: bool = Field(default=False, description="Whether or not the submission is saved")
    locked: bool = Field(default=False, description="Whether or not the submission has been locked")
    stickied: bool = Field(default=False, description="Whether or not the submission is stickied")
    spoiler: bool = Field(default=False, description="Whether or not the submission has been marked as a spoiler")
    over_18: bool = Field(default=False, description="Whether or not the submission has been marked as NSFW")
    is_original_content: bool = Field(
        default=False,
        description="Whether or not the submission has been set as original content"
    )
    is_self: bool = Field(
        default=False,
        description="Whether or not the submission is a selfpost (text-only)"
    )
    
    # Engagement metrics
    score: int = Field(default=0, description="The number of upvotes for the submission")
    upvote_ratio: float = Field(
        default=0.0,
        description="The percentage of upvotes from all votes on the submission (0.0 to 1.0)"
    )
    num_comments: int = Field(default=0, description="The number of comments on the submission")
    
    # Flair information
    link_flair_text: Optional[str] = Field(
        default=None,
        description="The link flair's text content, or None if not flaired"
    )
    link_flair_template_id: Optional[str] = Field(
        default=None,
        description="The link flair's template ID"
    )
    
    # Comments and Poll Data
    comments: List[RedditComment] = Field(
        default_factory=list,
        description="List of comments on the submission. CommentForest converted to list."
    )
    poll_data: Optional[PollData] = Field(
        default=None,
        description="Poll data if the submission is a poll, None otherwise"
    )
    
    @field_validator('edited')
    @classmethod
    def validate_edited(cls, v: Any) -> Union[bool, float]:
        """Validate edited field can be bool or float."""
        if isinstance(v, (bool, float, int)):
            return float(v) if isinstance(v, (int, float)) and v else bool(v)
        return False
    
    @field_validator('upvote_ratio')
    @classmethod
    def validate_upvote_ratio(cls, v: float) -> float:
        """Ensure upvote_ratio is between 0.0 and 1.0."""
        if v < 0.0:
            return 0.0
        if v > 1.0:
            return 1.0
        return v
    
    @classmethod
    def from_praw_submission(
        cls,
        submission: Any,
        include_comments: bool = True,
        comment_limit: Optional[int] = None,
        replace_more_comments: bool = True
    ) -> "RedditSubmission":
        """
        Create RedditSubmission from a PRAW Submission object.
        
        Args:
            submission: praw.reddit.models.Submission instance
            include_comments: Whether to fetch and include comments
            comment_limit: Maximum number of comments to fetch (None for all)
            replace_more_comments: Whether to replace "more comments" placeholders
            
        Returns:
            RedditSubmission model instance
        """
        # Extract author name (handle None for deleted users)
        author_name = None
        if hasattr(submission.author, 'name'):
            author_name = submission.author.name
        elif submission.author is not None:
            author_name = str(submission.author)
        
        # Extract subreddit name
        subreddit_name = submission.subreddit.display_name if hasattr(
            submission.subreddit, 'display_name'
        ) else str(submission.subreddit)
        
        # Process comments
        comments = []
        if include_comments:
            try:
                # Replace "more comments" placeholders if requested
                if replace_more_comments:
                    submission.comments.replace_more(limit=0)
                
                # Convert CommentForest to list
                comment_list = submission.comments.list()
                
                # Apply limit if specified
                if comment_limit is not None:
                    comment_list = comment_list[:comment_limit]
                
                # Convert each comment to RedditComment model
                comments = [
                    RedditComment.from_praw_comment(comment)
                    for comment in comment_list
                ]
            except Exception:
                # If comment fetching fails, continue without comments
                comments = []
        
        # Process poll data
        poll_data = None
        if hasattr(submission, 'poll_data') and submission.poll_data:
            try:
                poll_data = PollData.from_praw_poll_data(submission.poll_data)
            except Exception:
                # If poll data processing fails, continue without it
                poll_data = None
        
        return cls(
            id=submission.id,
            name=submission.name,
            author=author_name,
            author_flair_text=submission.author_flair_text,
            title=submission.title,
            selftext=submission.selftext or "",
            url=submission.url,
            permalink=submission.permalink,
            created_utc=submission.created_utc,
            edited=submission.edited,
            distinguished=submission.distinguished,
            subreddit=subreddit_name,
            clicked=submission.clicked,
            saved=submission.saved,
            locked=submission.locked,
            stickied=submission.stickied,
            spoiler=submission.spoiler,
            over_18=submission.over_18,
            is_original_content=submission.is_original_content,
            is_self=submission.is_self,
            score=submission.score,
            upvote_ratio=submission.upvote_ratio,
            num_comments=submission.num_comments,
            link_flair_text=submission.link_flair_text,
            link_flair_template_id=submission.link_flair_template_id,
            comments=comments,
            poll_data=poll_data,
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary, handling datetime conversion."""
        data = self.model_dump()
        # Convert created_utc to datetime if needed
        if 'created_utc' in data:
            data['created_datetime'] = datetime.fromtimestamp(data['created_utc'])
        return data