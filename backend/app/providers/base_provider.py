"""
Provider abstraction for ticket availability sources.

Any real integration MUST only use officially documented / publicly permitted
interfaces. Do not implement scraping that bypasses authentication, CAPTCHAs,
rate limits, or other access controls in any subclass of this interface.
"""
from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class MovieResult:
    external_id: str
    title: str
    language: Optional[str] = None
    poster_url: Optional[str] = None


@dataclass
class ShowResult:
    show_id: str
    provider: str
    cinema: str
    screen: Optional[str]
    show_time: str  # HH:MM
    available_seats: int
    adjacent_available: Optional[bool]  # None = cannot be determined
    booking_url: str


class TicketProvider(ABC):
    """Abstract interface every ticket data provider must implement."""

    name: str = "base"

    @abstractmethod
    async def search_movies(self, query: str, city: str) -> list[MovieResult]:
        ...

    @abstractmethod
    async def get_showtimes(self, movie_id: str, city: str, date: str) -> list[ShowResult]:
        ...

    @abstractmethod
    async def check_availability(self, show_id: str) -> ShowResult:
        ...

    @abstractmethod
    async def get_booking_url(self, show_id: str) -> str:
        ...
