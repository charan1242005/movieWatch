from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ShowOut(BaseModel):
    id: int
    tracker_id: int
    provider: str
    cinema: str
    screen: Optional[str] = None
    show_time: str
    available_seats: int
    adjacent_available: Optional[bool] = None
    booking_url: Optional[str] = None
    last_seen_at: datetime

    class Config:
        from_attributes = True
