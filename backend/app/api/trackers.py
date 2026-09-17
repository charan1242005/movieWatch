from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.tracker import Tracker, TrackerStatus
from app.models.user import User
from app.schemas.tracker import TrackerCreate, TrackerUpdate, TrackerOut
from app.services.movie_service import get_or_create_movie
from app.services.tracker_service import check_tracker
from app.utils.deps import get_current_user
from app.utils.logger import get_logger
from app.workers.availability_worker import schedule_tracker, unschedule_tracker

router = APIRouter(prefix="/api/trackers", tags=["trackers"])
logger = get_logger("trackers_api")


def _to_out(tracker: Tracker) -> TrackerOut:
    out = TrackerOut.model_validate(tracker)
    out.movie_title = tracker.movie.title if tracker.movie else None
    return out


@router.post("", response_model=TrackerOut, status_code=201)
async def create_tracker(payload: TrackerCreate, current_user: User = Depends(get_current_user),
                          db: Session = Depends(get_db)):
    movie = get_or_create_movie(db, payload.movie_title, payload.language)
    tracker = Tracker(
        user_id=current_user.id,
        movie_id=movie.id,
        city=payload.city,
        date=payload.date,
        platform=payload.platform,
        cinema=payload.cinema,
        language=payload.language,
        format=payload.format,
        start_time=payload.start_time,
        end_time=payload.end_time,
        seats_required=payload.seats_required,
        adjacent_seats=payload.adjacent_seats,
        check_interval=payload.check_interval,
        status=TrackerStatus.STOPPED,
    )
    db.add(tracker)
    db.commit()
    db.refresh(tracker)
    logger.info("Tracker created: %s (user=%s)", tracker.id, current_user.id)
    return _to_out(tracker)


@router.get("", response_model=list[TrackerOut])
def list_trackers(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    trackers = db.query(Tracker).filter(Tracker.user_id == current_user.id).order_by(Tracker.created_at.desc()).all()
    return [_to_out(t) for t in trackers]


def _get_owned_tracker(tracker_id: int, current_user: User, db: Session) -> Tracker:
    tracker = db.query(Tracker).filter(Tracker.id == tracker_id, Tracker.user_id == current_user.id).first()
    if not tracker:
        raise HTTPException(status_code=404, detail="Tracker not found")
    return tracker


@router.get("/{tracker_id}", response_model=TrackerOut)
def get_tracker(tracker_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _to_out(_get_owned_tracker(tracker_id, current_user, db))


@router.put("/{tracker_id}", response_model=TrackerOut)
def update_tracker(tracker_id: int, payload: TrackerUpdate, current_user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    tracker = _get_owned_tracker(tracker_id, current_user, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(tracker, field, value)
    db.commit()
    db.refresh(tracker)
    if tracker.status == TrackerStatus.ACTIVE:
        schedule_tracker(tracker.id, tracker.check_interval)
    logger.info("Tracker updated: %s", tracker.id)
    return _to_out(tracker)


@router.delete("/{tracker_id}", status_code=204)
def delete_tracker(tracker_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tracker = _get_owned_tracker(tracker_id, current_user, db)
    unschedule_tracker(tracker.id)
    db.delete(tracker)
    db.commit()
    logger.info("Tracker deleted: %s", tracker_id)
    return None


@router.post("/{tracker_id}/start", response_model=TrackerOut)
async def start_tracker(tracker_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tracker = _get_owned_tracker(tracker_id, current_user, db)
    tracker.status = TrackerStatus.ACTIVE
    db.commit()
    db.refresh(tracker)
    schedule_tracker(tracker.id, tracker.check_interval)
    logger.info("Tracker started: %s", tracker.id)
    # Run an immediate check so the UI has fresh data right away.
    await check_tracker(db, tracker)
    db.refresh(tracker)
    return _to_out(tracker)


@router.post("/{tracker_id}/stop", response_model=TrackerOut)
def stop_tracker(tracker_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tracker = _get_owned_tracker(tracker_id, current_user, db)
    tracker.status = TrackerStatus.STOPPED
    db.commit()
    db.refresh(tracker)
    unschedule_tracker(tracker.id)
    logger.info("Tracker stopped: %s", tracker.id)
    return _to_out(tracker)
