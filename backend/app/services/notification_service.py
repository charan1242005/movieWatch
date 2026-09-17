"""
Notification abstraction: email, Telegram, and in-app / browser-push records.

The app is designed to keep working end-to-end even when no real credentials
are configured — in that case, channels are skipped (status="skipped") but an
in_app notification row is always created so the frontend can display it.
"""
import smtplib
from email.mime.text import MIMEText
from sqlalchemy.orm import Session
import httpx

from app.config import settings
from app.models.notification import Notification
from app.models.tracker import Tracker
from app.models.user import User
from app.utils.logger import get_logger

logger = get_logger("notification_service")


def _send_email(to_email: str, subject: str, body: str) -> bool:
    if not (settings.email_host and settings.email_username and settings.email_password):
        logger.info("Email not configured — skipping email send")
        return False
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = settings.email_from
        msg["To"] = to_email
        with smtplib.SMTP(settings.email_host, settings.email_port, timeout=10) as server:
            server.starttls()
            server.login(settings.email_username, settings.email_password)
            server.sendmail(settings.email_from, [to_email], msg.as_string())
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("Email send failed: %s", exc)
        return False


import sys
import threading


def _play_desktop_alarm():
    """Trigger an audible siren/beep on Windows when tickets open."""
    if sys.platform == "win32":
        try:
            import winsound
            # Play a distinct 3-beep notification chime
            for freq in (880, 1174, 1760):
                winsound.Beep(freq, 250)
        except Exception as exc:
            logger.debug("Desktop sound beep failed: %s", exc)


async def _send_telegram(chat_id: str, text: str) -> bool:
    if not settings.telegram_bot_token or not chat_id:
        logger.info("Telegram not configured — skipping telegram send")
        return False
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                # Fallback to plain text if markdown parse fails
                await client.post(url, json={"chat_id": chat_id, "text": text})
            return resp.status_code == 200
    except Exception as exc:  # noqa: BLE001
        logger.error("Telegram send failed: %s", exc)
        return False


def build_message(tracker: Tracker, movie_title: str, show) -> str:
    screen_info = f" ({show.screen})" if show.screen else ""
    return (
        f"🚨 *TICKETS AVAILABLE / BOOKINGS OPENED!* 🎟️\n\n"
        f"🎬 *Movie*: {movie_title}\n"
        f"🎭 *Cinema*: {show.cinema}\n"
        f"📍 *City*: {tracker.city}\n"
        f"📅 *Date*: {tracker.date}\n"
        f"🕒 *Showtime*: {show.show_time}{screen_info}\n\n"
        f"⚡ *Book Now*:\n{show.booking_url}"
    )


async def notify_availability(db: Session, tracker: Tracker, user: User, movie_title: str, show) -> None:
    message = build_message(tracker, movie_title, show)

    # Always record an in-app notification so the frontend has something to show,
    # even if no external channel is configured.
    in_app = Notification(tracker_id=tracker.id, notification_type="in_app", message=message, status="sent")
    db.add(in_app)

    # Trigger audible desktop chime on local machine
    threading.Thread(target=_play_desktop_alarm, daemon=True).start()

    email_target = user.notify_email or user.email
    email_sent = _send_email(email_target, "MovieWatch: Tickets Available!", message)
    db.add(Notification(
        tracker_id=tracker.id, notification_type="email", message=message,
        status="sent" if email_sent else "skipped",
    ))

    telegram_sent = await _send_telegram(user.telegram_chat_id or "", message)
    db.add(Notification(
        tracker_id=tracker.id, notification_type="telegram", message=message,
        status="sent" if telegram_sent else "skipped",
    ))

    db.commit()
    logger.info("Notification generated for tracker %s (email_sent=%s, telegram_sent=%s)",
                tracker.id, email_sent, telegram_sent)
