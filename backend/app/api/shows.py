from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.tracker import Tracker
from app.models.show import Show
from app.models.user import User
from app.schemas.show import ShowOut
from app.utils.deps import get_current_user
from fastapi import HTTPException

router = APIRouter(prefix="/api/trackers", tags=["shows"])


@router.get("/{tracker_id}/shows", response_model=list[ShowOut])
def list_shows(tracker_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tracker = db.query(Tracker).filter(Tracker.id == tracker_id, Tracker.user_id == current_user.id).first()
    if not tracker:
        raise HTTPException(status_code=404, detail="Tracker not found")
    shows = db.query(Show).filter(Show.tracker_id == tracker_id).order_by(Show.show_time).all()
    return shows
