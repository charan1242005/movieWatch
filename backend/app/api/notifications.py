from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.notification import Notification
from app.models.tracker import Tracker
from app.models.user import User
from app.schemas.notification import NotificationOut, TestNotificationRequest
from app.utils.deps import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut])
def list_notifications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notifications = (
        db.query(Notification)
        .join(Tracker, Tracker.id == Notification.tracker_id)
        .filter(Tracker.user_id == current_user.id)
        .order_by(Notification.sent_at.desc())
        .limit(200)
        .all()
    )
    return notifications


@router.post("/test", response_model=NotificationOut)
async def send_test_notification(payload: TestNotificationRequest, current_user: User = Depends(get_current_user),
                                  db: Session = Depends(get_db)):
    tracker = db.query(Tracker).filter(Tracker.user_id == current_user.id).first()
    if not tracker:
        raise HTTPException(status_code=400, detail="Create at least one tracker before sending a test notification")
    notification = Notification(
        tracker_id=tracker.id, notification_type=payload.channel,
        message=payload.message, status="sent",
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification
