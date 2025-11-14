from typing import Literal

from pydantic import BaseModel

class RedditPost(BaseModel):
    platform: Literal["reddit"] = "reddit"