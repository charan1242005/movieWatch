from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.tracker import TrackerStatus, Platform


class TrackerCreate(BaseModel):
    movie_title: str = Field(..., description="Movie title; created if it doesn't exist")
    city: str
    date: str
    platform: Platform = Platform.MOCK
    cinema: str = "Any Cinema"
    language: Optional[str] = None
    format: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    seats_required: int = 1
    adjacent_seats: bool = False
    check_interval: int = 5


class TrackerUpdate(BaseModel):
    city: Optional[str] = None
    date: Optional[str] = None
    platform: Optional[Platform] = None
    cinema: Optional[str] = None
    language: Optional[str] = None
    format: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    seats_required: Optional[int] = None
    adjacent_seats: Optional[bool] = None
    check_interval: Optional[int] = None


class TrackerOut(BaseModel):
    id: int
    user_id: int
    movie_id: int
    movie_title: Optional[str] = None
    city: str
    date: str
    platform: Platform
    cinema: str
    language: Optional[str] = None
    format: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    seats_required: int
    adjacent_seats: bool
    status: TrackerStatus
    check_interval: int
    last_checked_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
