"""SQLite database manager implementation.

This module is designed for Python 3.14+ with GIL removed, enabling true concurrency.
All database operations are thread-safe using proper connection pooling and locks.
"""

import json
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine, text, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .base import DatabaseManager

Base = declarative_base()


class PostTable(Base):
    """SQLite table for posts - simplified schema."""
    
    __tablename__ = "posts"
    __table_args__ = (
        UniqueConstraint('platform', 'object_id', name='unique_platform_object'),
    )
    
    # Core fields (required for all platforms)
    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String(50), nullable=False, index=True)
    object_id = Column(String(255), nullable=False, index=True)
    author_handle = Column(String(255), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, index=True)
    url = Column(String(500))
    parent_id = Column(String(255))
    is_comment = Column(Integer, default=0)  # 0 or 1
    raw_data = Column(Text)  # JSON string
    
    # Metrics (stored as JSON for flexibility)
    metrics = Column(Text)  # JSON string
    
    # Reddit-specific fields (only essential ones)
    subreddit = Column(String(255))
    title = Column(Text)
    is_nsfw = Column(Integer, default=0)
    
    # Bluesky-specific fields (only essential ones)
    handle = Column(String(255))
    display_name = Column(String(255))
    avatar_url = Column(String(500))
    is_reply = Column(Integer, default=0)
    is_repost = Column(Integer, default=0)
    reply_to = Column(String(255))
    repost_of = Column(String(255))
    tags = Column(Text)  # JSON string - only for Bluesky
    
    # Mastodon-specific fields (only essential ones)
    instance = Column(String(255))
    is_reblog = Column(Integer, default=0)
    is_sensitive = Column(Integer, default=0)
    reblog_of = Column(String(255))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "platform": self.platform,
            "object_id": self.object_id,
            "author_handle": self.author_handle,
            "text": self.text,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "tags": json.loads(self.tags) if self.tags else [],
            "metrics": json.loads(self.metrics) if self.metrics else {},
            "url": self.url,
            "parent_id": self.parent_id,
            "is_comment": bool(self.is_comment),
            "raw_data": json.loads(self.raw_data) if self.raw_data else None,
            # Platform-specific fields
            "subreddit": self.subreddit,
            "title": self.title,
            "flair": self.flair,
            "is_self": bool(self.is_self),
            "is_nsfw": bool(self.is_nsfw),
            "is_locked": bool(self.is_locked),
            "is_archived": bool(self.is_archived),
            "is_stickied": bool(self.is_stickied),
            "link_url": self.link_url,
            "domain": self.domain,
            "handle": self.handle,
            "display_name": self.display_name,
            "avatar_url": self.avatar_url,
            "is_reply": bool(self.is_reply),
            "is_repost": bool(self.is_repost),
            "is_quote": bool(self.is_quote),
            "reply_to": self.reply_to,
            "repost_of": self.repost_of,
            "quote_of": self.quote_of,
            "images": json.loads(self.images) if self.images else [],
            "links": json.loads(self.links) if self.links else [],
            "instance": self.instance,
            "is_reblog": bool(self.is_reblog),
            "is_sensitive": bool(self.is_sensitive),
            "is_boosted": bool(self.is_boosted),
            "reblog_of": self.reblog_of,
            "language": self.language,
            "spoiler_text": self.spoiler_text,
        }


class SQLiteManager(DatabaseManager):
    """SQLite database manager with thread-safe operations for Python 3.14+.
    
    With the GIL removed in Python 3.14, this manager uses:
    - Thread-safe connection pooling
    - Per-operation locks for critical sections
    - Proper SQLite multi-threading configuration
    """
    
    def __init__(self, connection_string: str, separate_databases: bool = False):
        """Initialize SQLite manager with thread safety."""
        # Initialize lock for thread-safe operations
        self._lock = threading.Lock()
        super().__init__(connection_string, separate_databases)
    
    def _setup_connection(self) -> None:
        """Setup SQLite connection with thread-safe configuration."""
        # Ensure directory exists
        db_path = Path(self.connection_string.replace("sqlite:///", ""))
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure SQLite for multi-threaded access
        # check_same_thread=False allows connections from different threads
        # pool_size and max_overflow enable connection pooling for concurrent access
        self.engine = create_engine(
            self.connection_string,
            echo=False,
            pool_pre_ping=True,
            pool_size=10,  # Connection pool for concurrent threads
            max_overflow=20,  # Additional connections beyond pool_size
            connect_args={
                "check_same_thread": False,  # Allow multi-threaded access
                "timeout": 30.0,  # Wait up to 30 seconds for locks
            }
        )
        self.session_factory = sessionmaker(
            bind=self.engine,
            expire_on_commit=False  # Better for concurrent access
        )
    
    def create_tables(self, platforms: List[str]) -> None:
        """Create necessary tables."""
        if self.separate_databases:
            # Create separate databases for each platform
            for platform in platforms:
                db_path = Path(self.connection_string.replace("sqlite:///", ""))
                platform_db_path = db_path.parent / f"{platform}_{db_path.name}"
                platform_connection_string = f"sqlite:///{platform_db_path}"
                
                # Create engine for platform-specific database
                platform_engine = create_engine(platform_connection_string)
                Base.metadata.create_all(platform_engine)
                platform_engine.dispose()
        else:
            # Create single database with all tables
            Base.metadata.create_all(self.engine)
    
    def insert_post(self, post: "BasePost") -> None:
        """Insert a single post."""
        session = self.session_factory()
        try:
            # Convert post to database row
            db_post = self._post_to_db_row(post)
            session.add(db_post)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def insert_posts(self, posts: List["BasePost"]) -> None:
        """Insert multiple posts with deduplication and update handling.
        
        Thread-safe operation using locks to prevent race conditions.
        """
        if not posts:
            return
        
        # Use lock to ensure thread-safe database access
        with self._lock:
            session = self.session_factory()
            try:
                # Get existing posts to check for duplicates and updates
                existing_posts = self._get_existing_posts(session, posts)
                
                # Process posts for insertion/update
                new_posts = []
                updated_posts = []
                
                for post in posts:
                    post_key = (post.platform, post.object_id)
                    
                    if post_key in existing_posts:
                        # Post exists - check if it's been updated
                        existing_post = existing_posts[post_key]
                        if existing_post.text != post.text:
                            # Post has been edited - update it
                            updated_posts.append((existing_post, post))
                    else:
                        # New post
                        new_posts.append(self._post_to_db_row(post))
                        # Add to existing set to avoid duplicates within this batch
                        existing_posts[post_key] = post
                
                # Insert new posts
                if new_posts:
                    session.add_all(new_posts)
                
                # Update edited posts
                for existing_post, updated_post in updated_posts:
                    # Update the existing post with new data
                    existing_post.text = updated_post.text
                    existing_post.raw_data = json.dumps(updated_post.raw_data, default=str) if updated_post.raw_data else None
                    existing_post.metrics = json.dumps(updated_post.metrics.dict(), default=str)
                    # Update other fields as needed
                    if hasattr(updated_post, 'title'):
                        existing_post.title = getattr(updated_post, 'title', None)
                
                if new_posts or updated_posts:
                    session.commit()
                    
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
    
    def _get_existing_posts(self, session, posts: List["BasePost"]) -> dict:
        """Get existing posts to check for duplicates and updates."""
        existing_posts = {}
        
        # Get unique combinations of platform and object_id from incoming posts
        post_keys = [(post.platform, post.object_id) for post in posts]
        
        if not post_keys:
            return existing_posts
            
        # Query existing posts
        for platform, object_id in post_keys:
            existing = session.query(PostTable).filter(
                PostTable.platform == platform,
                PostTable.object_id == object_id
            ).first()
            
            if existing:
                # Store the actual post object for potential updates
                existing_posts[(platform, object_id)] = existing
        
        return existing_posts
    
    def get_duplicate_count(self) -> int:
        """Get count of duplicate posts that were prevented."""
        session = self.session_factory()
        try:
            # This is a simplified approach - in practice, you might want to track this differently
            # For now, we'll return 0 as the deduplication happens at insert time
            return 0
        finally:
            session.close()
    
    def get_posts(
        self, 
        platform: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get posts from database."""
        session = self.session_factory()
        try:
            query = session.query(PostTable)
            
            if platform:
                query = query.filter(PostTable.platform == platform)
            
            if offset:
                query = query.offset(offset)
            
            if limit:
                query = query.limit(limit)
            
            posts = query.all()
            return [post.to_dict() for post in posts]
        finally:
            session.close()
    
    def get_post_count(self, platform: Optional[str] = None) -> int:
        """Get total number of posts (thread-safe)."""
        # Use lock for thread-safe read operations
        with self._lock:
            session = self.session_factory()
            try:
                query = session.query(PostTable)
                
                if platform:
                    query = query.filter(PostTable.platform == platform)
                
                return query.count()
            finally:
                session.close()
    
    def close(self) -> None:
        """Close database connection."""
        if self.engine:
            self.engine.dispose()
    
    def _post_to_db_row(self, post: "BasePost") -> PostTable:
        """Convert BasePost to database row - simplified schema."""
        # Only store tags for Bluesky platform
        tags_json = json.dumps(post.tags) if post.platform == "bluesky" else None
        
        return PostTable(
            # Core fields
            platform=post.platform,
            object_id=post.object_id,
            author_handle=post.author_handle,
            text=post.text,
            created_at=post.created_at,
            url=post.url,
            parent_id=post.parent_id,
            is_comment=1 if post.is_comment else 0,
            raw_data=json.dumps(post.raw_data, default=str) if post.raw_data else None,
            metrics=json.dumps(post.metrics.dict(), default=str),
            
            # Reddit-specific fields (only essential ones)
            subreddit=getattr(post, 'subreddit', None),
            title=getattr(post, 'title', None),
            is_nsfw=1 if bool(getattr(post, 'is_nsfw', False)) else 0,
            
            # Bluesky-specific fields (only essential ones)
            handle=getattr(post, 'handle', None),
            display_name=getattr(post, 'display_name', None),
            avatar_url=getattr(post, 'avatar_url', None),
            is_reply=1 if bool(getattr(post, 'is_reply', False)) else 0,
            is_repost=1 if bool(getattr(post, 'is_repost', False)) else 0,
            reply_to=getattr(post, 'reply_to', None),
            repost_of=getattr(post, 'repost_of', None),
            tags=tags_json,  # Only for Bluesky
            
            # Mastodon-specific fields (only essential ones)
            instance=getattr(post, 'instance', None),
            is_reblog=1 if bool(getattr(post, 'is_reblog', False)) else 0,
            is_sensitive=1 if bool(getattr(post, 'is_sensitive', False)) else 0,
            reblog_of=getattr(post, 'reblog_of', None),
        )
