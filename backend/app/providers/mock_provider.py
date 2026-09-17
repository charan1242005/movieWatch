"""
MockTicketProvider

Fully self-contained, deterministic-ish simulation of a ticket provider so the
entire tracker -> worker -> notification pipeline can be developed and tested
without connecting to any real, third-party service.

Simulation model
-----------------
Each (movie_id, city, date) "showset" starts in state MOVIE_NOT_AVAILABLE.
After `reveal_after_seconds` (config, default from settings) it transitions to
SHOW_AVAILABLE with a handful of generated shows, each with 0 seats
(SEATS_SOLD_OUT). After a further short delay, seats open up
(SEATS_AVAILABLE) with a random-ish (but deterministic per run) seat count.

A developer/admin endpoint (see app/api/movies.py `POST
/api/dev/mock/force-state`) allows forcing any of the simulation states
instantly for demos and tests:

    MOVIE_NOT_AVAILABLE
    SHOW_NOT_AVAILABLE
    SHOW_AVAILABLE
    SEATS_AVAILABLE
    SEATS_SOLD_OUT
"""
import enum
import time
import hashlib
from typing import Optional
from app.providers.base_provider import TicketProvider, MovieResult, ShowResult
from app.config import settings

CINEMAS = ["PVR INOX", "Cinepolis", "Miraj Cinemas", "Asian Multiplex"]


class MockState(str, enum.Enum):
    MOVIE_NOT_AVAILABLE = "MOVIE_NOT_AVAILABLE"
    SHOW_NOT_AVAILABLE = "SHOW_NOT_AVAILABLE"
    SHOW_AVAILABLE = "SHOW_AVAILABLE"
    SEATS_AVAILABLE = "SEATS_AVAILABLE"
    SEATS_SOLD_OUT = "SEATS_SOLD_OUT"


# In-memory simulation registry: key -> {"created_at": ts, "forced_state": Optional[MockState]}
_SIM_REGISTRY: dict[str, dict] = {}


def _key(movie_id: str, city: str, date: str) -> str:
    return f"{movie_id}|{city}|{date}".lower()


def force_state(movie_id: str, city: str, date: str, state: Optional[str]) -> None:
    """Developer/admin hook: force a simulation state, or clear it (state=None)."""
    k = _key(movie_id, city, date)
    entry = _SIM_REGISTRY.setdefault(k, {"created_at": time.time(), "forced_state": None})
    entry["forced_state"] = MockState(state) if state else None


def reset_simulation(movie_id: str, city: str, date: str) -> None:
    k = _key(movie_id, city, date)
    _SIM_REGISTRY.pop(k, None)


def _seed_int(key: str, salt: str) -> int:
    h = hashlib.sha256(f"{key}:{salt}".encode()).hexdigest()
    return int(h[:8], 16)


def _current_state(movie_id: str, city: str, date: str) -> MockState:
    k = _key(movie_id, city, date)
    entry = _SIM_REGISTRY.setdefault(k, {"created_at": time.time(), "forced_state": None})
    if entry["forced_state"] is not None:
        return entry["forced_state"]

    elapsed = time.time() - entry["created_at"]
    delay = settings.mock_provider_availability_delay_seconds

    if elapsed < delay:
        return MockState.MOVIE_NOT_AVAILABLE
    elif elapsed < delay * 2:
        return MockState.SHOW_AVAILABLE  # shows exist, 0 seats
    else:
        return MockState.SEATS_AVAILABLE


class MockTicketProvider(TicketProvider):
    name = "mock"

    async def search_movies(self, query: str, city: str) -> list[MovieResult]:
        if not query:
            return []
        return [
            MovieResult(
                external_id=f"mock-{query.lower().replace(' ', '-')}",
                title=query.title(),
                language="English",
                poster_url=None,
            )
        ]

    async def get_showtimes(self, movie_id: str, city: str, date: str) -> list[ShowResult]:
        state = _current_state(movie_id, city, date)

        if state in (MockState.MOVIE_NOT_AVAILABLE, MockState.SHOW_NOT_AVAILABLE):
            return []

        shows: list[ShowResult] = []
        times = ["14:00", "17:30", "19:30", "22:00"]
        for i, cinema in enumerate(CINEMAS):
            show_time = times[i % len(times)]
            show_id = f"{_key(movie_id, city, date)}::{cinema}::{show_time}".replace(" ", "-")

            if state == MockState.SEATS_SOLD_OUT:
                seats = 0
            elif state == MockState.SEATS_AVAILABLE:
                seats = 2 + (_seed_int(show_id, "seats") % 12)
            else:  # SHOW_AVAILABLE: shows exist, no seats yet
                seats = 0

            adjacent = seats >= 2

            shows.append(
                ShowResult(
                    show_id=show_id,
                    provider=self.name,
                    cinema=cinema,
                    screen=f"Screen {1 + (i % 3)}",
                    show_time=show_time,
                    available_seats=seats,
                    adjacent_available=adjacent if seats > 0 else False,
                    booking_url=f"https://mock-booking.example.com/book/{show_id}",
                )
            )
        return shows

    async def check_availability(self, show_id: str) -> ShowResult:
        parts = show_id.split("::")
        key_part = parts[0] if parts else show_id
        movie_id, city, date = (key_part.split("|") + ["", "", ""])[:3]
        shows = await self.get_showtimes(movie_id, city, date)
        for s in shows:
            if s.show_id == show_id:
                return s
        return ShowResult(
            show_id=show_id, provider=self.name, cinema="Unknown", screen=None,
            show_time="00:00", available_seats=0, adjacent_available=False,
            booking_url=f"https://mock-booking.example.com/book/{show_id}",
        )

    async def get_booking_url(self, show_id: str) -> str:
        return f"https://mock-booking.example.com/book/{show_id}"
