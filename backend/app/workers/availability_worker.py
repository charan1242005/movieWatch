"""
Background scheduler that polls each active tracker on its own configured
interval, using APScheduler with per-tracker jobs (so trackers with
different check_interval values are respected independently, and provider
rate limits are naturally bounded by each tracker's own interval).
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.database import SessionLocal
from app.models.tracker import Tracker, TrackerStatus
from app.services.tracker_service import run_check_for_tracker_id
from app.utils.logger import get_logger

logger = get_logger("availability_worker")

MIN_INTERVAL_SECONDS = 30  # sensible floor so no provider is hit too often

# APScheduler instances cannot be restarted once shut down, so we hold a
# reference that gets replaced on each start_scheduler() call (this also
# keeps repeated app startup/shutdown cycles, e.g. in tests, safe).
scheduler = AsyncIOScheduler()


def _job_id(tracker_id: int) -> str:
    return f"tracker-check-{tracker_id}"


def schedule_tracker(tracker_id: int, interval_value: int) -> None:
    if not scheduler.running:
        return
    # If interval_value >= 10, treat as direct seconds (e.g. 30s, 45s, 60s);
    # otherwise treat as minutes (e.g. 1 min -> 60s). Floor at MIN_INTERVAL_SECONDS (30s).
    if interval_value >= 10:
        seconds = max(interval_value, MIN_INTERVAL_SECONDS)
    else:
        seconds = max(interval_value * 60, MIN_INTERVAL_SECONDS)
    scheduler.add_job(
        run_check_for_tracker_id,
        trigger=IntervalTrigger(seconds=seconds),
        args=[tracker_id],
        id=_job_id(tracker_id),
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    logger.info("Scheduled tracker %s every %ss", tracker_id, seconds)


def unschedule_tracker(tracker_id: int) -> None:
    if not scheduler.running:
        return
    job_id = _job_id(tracker_id)
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info("Unscheduled tracker %s", tracker_id)


def start_scheduler() -> None:
    global scheduler
    if scheduler.running:
        scheduler.shutdown(wait=False)
    scheduler = AsyncIOScheduler()
    scheduler.start()
    logger.info("Availability worker scheduler started")

    # Re-schedule any trackers that were active before a restart.
    db = SessionLocal()
    try:
        active = db.query(Tracker).filter(Tracker.status == TrackerStatus.ACTIVE).all()
        for tracker in active:
            schedule_tracker(tracker.id, tracker.check_interval)
    finally:
        db.close()


def shutdown_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Availability worker scheduler stopped")
