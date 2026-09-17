import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class TrackerStatus(str, enum.Enum):
    ACTIVE = "active"
    STOPPED = "stopped"
    FULFILLED = "fulfilled"


class Platform(str, enum.Enum):
    BOOKMYSHOW = "bookmyshow"
    DISTRICT = "district"
    BOTH = "both"
    MOCK = "mock"


class Tracker(Base):
    __tablename__ = "trackers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)

    city = Column(String, nullable=False)
    date = Column(String, nullable=False)  # YYYY-MM-DD
    platform = Column(Enum(Platform), default=Platform.MOCK, nullable=False)
    cinema = Column(String, default="Any Cinema")
    language = Column(String, nullable=True)
    format = Column(String, nullable=True)  # 2D/3D/IMAX etc
    start_time = Column(String, nullable=True)  # HH:MM
    end_time = Column(String, nullable=True)  # HH:MM
    seats_required = Column(Integer, default=1)
    adjacent_seats = Column(Boolean, default=False)

    status = Column(Enum(TrackerStatus), default=TrackerStatus.STOPPED, nullable=False)
    check_interval = Column(Integer, default=5)  # minutes
    last_checked_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="trackers")
    movie = relationship("Movie")
    shows = relationship("Show", back_populates="tracker", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="tracker", cascade="all, delete-orphan")
