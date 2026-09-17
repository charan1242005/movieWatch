"""
Core tracker/availability-checking logic using the permitted public-page providers.
"""
from datetime import datetime, timezone, time as dtime
from sqlalchemy.orm import Session
from app.models.tracker import Tracker, TrackerStatus, Platform
from app.models.show import Show
from app.models.movie import Movie
from app.providers.mock_provider import MockTicketProvider
from app.providers.public_page_provider import PublicPageProvider
from app.services.notification_service import notify_availability
from app.database import SessionLocal
from app.utils.logger import get_logger

logger = get_logger("tracker_service")
_PROVIDERS = {
    Platform.MOCK: MockTicketProvider(),
    Platform.BOOKMYSHOW: PublicPageProvider("bookmyshow"),
    Platform.DISTRICT: PublicPageProvider("district"),
}

def _providers_for(platform: Platform) -> list:
    if platform == Platform.BOTH:
        return [_PROVIDERS[Platform.BOOKMYSHOW], _PROVIDERS[Platform.DISTRICT]]
    return [_PROVIDERS[platform]]

def _time_in_range(show_time: str, start: str | None, end: str | None) -> bool:
    if not start or not end:
        return True
    try:
        st, et, ct = dtime.fromisoformat(start), dtime.fromisoformat(end), dtime.fromisoformat(show_time)
        return st <= ct <= et if st <= et else ct >= st or ct <= et
    except ValueError:
        return True

async def check_tracker(db: Session, tracker: Tracker) -> list[Show]:
    movie = db.query(Movie).filter(Movie.id == tracker.movie_id).first()
    if not movie:
        return []
    matched_shows: list[Show] = []
    for provider in _providers_for(tracker.platform):
        try:
            results = await provider.get_showtimes(movie.external_id, tracker.city, tracker.date)
        except Exception as exc:
            logger.warning("Provider %s check failed for tracker %s: %s", provider.name, tracker.id, exc)
            continue
        for result in results:
            if tracker.cinema and tracker.cinema.lower() != "any cinema" and tracker.cinema.lower() not in result.cinema.lower():
                continue
            if not _time_in_range(result.show_time, tracker.start_time, tracker.end_time):
                continue
            existing = db.query(Show).filter(
                Show.tracker_id == tracker.id,
                Show.provider == result.provider,
                Show.cinema == result.cinema,
                Show.show_time == result.show_time,
            ).first()
            previously_available = bool(existing and existing.available_seats >= tracker.seats_required and (not tracker.adjacent_seats or existing.adjacent_available))
            if existing:
                existing.available_seats = result.available_seats
                existing.adjacent_available = result.adjacent_available
                existing.booking_url = result.booking_url
                existing.last_seen_at = datetime.now(timezone.utc)
                show_row = existing
            else:
                show_row = Show(
                    tracker_id=tracker.id, provider=result.provider, cinema=result.cinema,
                    screen=result.screen, show_time=result.show_time,
                    available_seats=result.available_seats, adjacent_available=result.adjacent_available,
                    booking_url=result.booking_url,
                )
                db.add(show_row)
            db.commit(); db.refresh(show_row); matched_shows.append(show_row)
            now_available = show_row.available_seats >= tracker.seats_required and (not tracker.adjacent_seats or show_row.adjacent_available)
            if now_available and not previously_available:
                await notify_availability(db, tracker, tracker.user, movie.title, show_row)
                tracker.status = TrackerStatus.ACTIVE
    tracker.last_checked_at = datetime.now(timezone.utc)
    db.commit()
    return matched_shows

async def run_check_for_tracker_id(tracker_id: int) -> None:
    db = SessionLocal()
    try:
        tracker = db.query(Tracker).filter(Tracker.id == tracker_id).first()
        if tracker and tracker.status == TrackerStatus.ACTIVE:
            await check_tracker(db, tracker)
    except Exception as exc:
        logger.error("Error checking tracker %s: %s", tracker_id, exc)
    finally:
        db.close()
