from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class Show(Base):
    __tablename__ = "shows"

    id = Column(Integer, primary_key=True, index=True)
    tracker_id = Column(Integer, ForeignKey("trackers.id"), nullable=False)
    provider = Column(String, nullable=False)
    cinema = Column(String, nullable=False)
    screen = Column(String, nullable=True)
    show_time = Column(String, nullable=False)  # HH:MM
    available_seats = Column(Integer, default=0)
    adjacent_available = Column(Boolean, nullable=True)  # None = unknown
    booking_url = Column(String, nullable=True)
    last_seen_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    tracker = relationship("Tracker", back_populates="shows")
