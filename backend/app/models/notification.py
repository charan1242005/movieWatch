from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    tracker_id = Column(Integer, ForeignKey("trackers.id"), nullable=False)
    notification_type = Column(String, nullable=False)  # email, telegram, push, in_app
    message = Column(String, nullable=False)
    sent_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String, default="sent")  # sent, failed, skipped

    tracker = relationship("Tracker", back_populates="notifications")
