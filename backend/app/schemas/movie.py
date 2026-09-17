from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MovieOut(BaseModel):
    id: int
    title: str
    external_id: Optional[str] = None
    language: Optional[str] = None
    poster_url: Optional[str] = None

    class Config:
        from_attributes = True
