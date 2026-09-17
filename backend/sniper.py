import time
import asyncio
import sys
import argparse
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.providers.bookmyshow_provider import BookMyShowProvider
from app.providers.district_provider import DistrictProvider
from app.services.notification_service import _send_telegram, _play_desktop_alarm
from app.config import settings


async def run_sniper(movie: str, city: str, date: str, theatres_raw: str, interval: int, platform: str, once: bool = False):
    targets = [
        t.strip().lower()
        for t in theatres_raw.replace("+", ",").replace("|", ",").split(",")
        if t.strip() and t.strip().lower() not in ("all", "any", "any cinema")
    ]

    print("=" * 60)
    print("  🎬 MOVIEWATCH TICKET SNIPER ACTIVE")
    print("=" * 60)
    print(f"Movie:        {movie}")
    print(f"City:         {city}")
    print(f"Date:         {date}")
    print(f"Theatres:     {theatres_raw if targets else 'ALL THEATRES'}")
    print(f"Platform:     {platform.upper()}")
    print(f"Interval:     Every {interval} seconds")
    print("=" * 60)
    print("Tracker is active. You can minimize this window and leave it running.")
    print("Press Ctrl+C to stop.\n")

    bms = BookMyShowProvider()
    district = DistrictProvider()

    seen_shows = set()
    checks_count = 0

    while True:
        checks_count += 1
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        all_found = []

        # 1. BookMyShow check
        if platform.lower() in ("bookmyshow", "both", "bms"):
            try:
                movies = await bms.search_movies(movie, city)
                if movies:
                    mid = movies[0].external_id
                    shows = await bms.get_showtimes(mid, city, date)
                    all_found.extend(shows)
            except Exception as e:
                print(f"[{now_str}] BMS check error: {e}")

        # 2. District check
        if platform.lower() in ("district", "both"):
            try:
                d_movies = await district.search_movies(movie, city)
                if d_movies:
                    d_mid = d_movies[0].external_id
                    d_shows = await district.get_showtimes(d_mid, city, date)
                    all_found.extend(d_shows)
            except Exception as e:
                print(f"[{now_str}] District check error: {e}")

        # Match against target theatres
        matched = []
        for show in all_found:
            if targets:
                if not any(t in show.cinema.lower() for t in targets):
                    continue
            matched.append(show)

        # Detect new openings
        new_openings = []
        for s in matched:
            key = f"{s.provider}::{s.cinema}::{s.show_time}"
            if key not in seen_shows:
                seen_shows.add(key)
                new_openings.append(s)

        if new_openings:
            print(f"\n🚨🚨🚨 [{now_str}] TICKETS OPENED FOR BOOKING! 🎟️")
            _play_desktop_alarm()

            for s in new_openings:
                print(f"  🎭 Cinema:   {s.cinema}")
                print(f"  🕒 Showtime: {s.show_time} ({s.screen})")
                print(f"  🔗 Book Now: {s.booking_url}\n")

                msg = (
                    f"🚨 *TICKETS AVAILABLE / BOOKINGS OPENED!* 🎟️\n\n"
                    f"🎬 *Movie*: {movie}\n"
                    f"🎭 *Cinema*: {s.cinema}\n"
                    f"📍 *City*: {city}\n"
                    f"📅 *Date*: {date}\n"
                    f"🕒 *Showtime*: {s.show_time} ({s.screen})\n\n"
                    f"⚡ *Book Now*:\n{s.booking_url}"
                )
                if settings.telegram_chat_id:
                    await _send_telegram(settings.telegram_chat_id, msg)
        else:
            print(f"[{now_str}] Check #{checks_count}: ⏳ Waiting for bookings to open... (0 matching shows)")

        if once:
            break
        await asyncio.sleep(interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MovieWatch Standalone Sniper")
    parser.add_argument("--movie", type=str, default="Devara", help="Movie name or BMS link/event code")
    parser.add_argument("--city", type=str, default="Visakhapatnam", help="City name")
    parser.add_argument("--date", type=str, default="2026-09-25", help="Date YYYY-MM-DD")
    parser.add_argument("--theatres", type=str, default="PVR CMR Central + INOX + Asian", help="Theatres filter")
    parser.add_argument("--interval", type=int, default=30, help="Polling interval in seconds")
    parser.add_argument("--platform", type=str, default="both", help="Platform: bms, district, or both")
    parser.add_argument("--once", action="store_true", help="Run a single check and exit")

    args = parser.parse_args()

    try:
        asyncio.run(run_sniper(args.movie, args.city, args.date, args.theatres, args.interval, args.platform, once=args.once))
    except KeyboardInterrupt:
        print("\nMovieWatch Sniper stopped by user.")
