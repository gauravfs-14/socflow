from pydantic_settings import BaseSettings
from datetime import datetime

class Settings(BaseSettings):
    reddit: RedditSettings

class RedditSettings(BaseSettings):
    client_id: str
    client_secret: str
    username: str
    password: str
    subreddits: list[str]
    keywords: list[str]
    start_date: datetime
    end_date: datetime