from pydantic import BaseModel
from datetime import datetime


class NotificationOut(BaseModel):
    id: int
    tracker_id: int
    notification_type: str
    message: str
    sent_at: datetime
    status: str

    class Config:
        from_attributes = True


class TestNotificationRequest(BaseModel):
    channel: str = "email"
    message: str = "This is a test notification from MovieWatch."
