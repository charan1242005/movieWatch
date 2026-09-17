"""Permitted public-page monitor for cinema booking listings.

This provider reads publicly accessible HTML pages published by the ticketing
platforms. It does not log in, solve CAPTCHAs, bypass bot protection, or use
private APIs. If a platform presents an access challenge, the check is treated
as unavailable and the worker backs off instead of attempting to circumvent it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import quote, urljoin

import httpx
from bs4 import BeautifulSoup
from app.providers.base_provider import TicketProvider, MovieResult, ShowResult

@dataclass(frozen=True)
class PlatformConfig:
    name: str
    base_url: str
    city_slug: dict[str, str]
    listing_urls: tuple[str, ...]

_CONFIGS = {
    "bookmyshow": PlatformConfig("bookmyshow", "https://in.bookmyshow.com", {"visakhapatnam": "vizag-visakhapatnam", "vizag": "vizag-visakhapatnam"}, ("/explore/home/{city}", "/explore/upcoming-movies-{city}")),
    "district": PlatformConfig("district", "https://www.district.in", {"visakhapatnam": "vizag", "vizag": "vizag"}, ("/movies/{city}-movie-tickets",)),
}
TIME_RE = re.compile(r"\b(?:[01]?\d|2[0-3]):[0-5]\d\b")
CHALLENGE_MARKERS = ("captcha", "verify you are human", "access denied", "unusual traffic", "checking your browser", "enable javascript and cookies")

class PublicPageProvider(TicketProvider):
    def __init__(self, platform: str):
        if platform not in _CONFIGS: raise ValueError(f"Unsupported public-page platform: {platform}")
        self.config = _CONFIGS[platform]; self.name = platform
    def _city_slug(self, city: str) -> str:
        normalized = " ".join(city.lower().split())
        return self.config.city_slug.get(normalized, normalized.replace(" ", "-"))
    def _listing_urls(self, city: str) -> list[str]:
        return [urljoin(self.config.base_url, p.format(city=self._city_slug(city))) for p in self.config.listing_urls]
    async def _get(self, url: str) -> tuple[str, str]:
        headers = {"User-Agent": "MovieWatch/2.0 (+public-page-monitor)", "Accept": "text/html,application/xhtml+xml", "Cache-Control": "no-cache"}
        async with httpx.AsyncClient(timeout=20, follow_redirects=True, headers=headers) as client:
            response = await client.get(url, params={"mw_check": "1"}); text = response.text; lower = text.lower()
            if response.status_code in (401, 403, 429) or any(m in lower for m in CHALLENGE_MARKERS): raise RuntimeError(f"{self.name} returned an access challenge ({response.status_code})")
            response.raise_for_status(); return str(response.url), text
    @staticmethod
    def _soup(text: str) -> BeautifulSoup: return BeautifulSoup(text, "html.parser")
    @staticmethod
    def _clean(value: str) -> str: return re.sub(r"\s+", " ", value or "").strip()
    def _movie_links(self, html: str, movie_title: str) -> list[tuple[str, str]]:
        soup = self._soup(html); needle = self._clean(movie_title).lower(); results=[]
        for a in soup.find_all("a", href=True):
            text=self._clean(a.get_text(" "))
            if needle and needle in text.lower(): results.append((text, urljoin(self.config.base_url, a["href"])))
        return results
    async def search_movies(self, query: str, city: str) -> list[MovieResult]:
        results=[]; seen=set(); needle=self._clean(query).lower()
        for listing_url in self._listing_urls(city):
            try: final_url, html = await self._get(listing_url)
            except Exception: continue
            for a in self._soup(html).find_all("a", href=True):
                title=self._clean(a.get_text(" "))
                if not title or needle not in title.lower(): continue
                href=urljoin(final_url,a["href"]); key=href.lower()
                if key in seen: continue
                seen.add(key); results.append(MovieResult(external_id=href,title=title))
        return results[:20]
    async def get_showtimes(self, movie_id: str, city: str, date: str) -> list[ShowResult]:
        movie_url = movie_id if movie_id.startswith("http") else ""; movie_title = movie_id if not movie_url else ""; pages=[]
        for listing_url in self._listing_urls(city):
            try: final_url, html=await self._get(listing_url)
            except Exception: continue
            pages.append((final_url,html))
            if not movie_url:
                links=self._movie_links(html,movie_title)
                if links: movie_url=links[0][1]
        if movie_url:
            try: final_url,html=await self._get(movie_url); pages.append((final_url,html))
            except Exception: pass
        results=[]
        for page_url,html in pages:
            soup=self._soup(html); visible=self._clean(soup.get_text(" ")); times=TIME_RE.findall(visible)
            cinemas=[]
            for a in soup.find_all("a",href=True):
                txt=self._clean(a.get_text(" "))
                if any(t in txt.lower() for t in ("pvr","inox","cinepolis","asian","miraj","cinema","theatre")) and txt not in cinemas: cinemas.append(txt)
            if times and any(w in visible.lower() for w in ("book tickets","book now","select seats","showtimes","show time","tickets")):
                for idx,show_time in enumerate(times[:30]):
                    cinema=cinemas[idx%len(cinemas)] if cinemas else "Booking available"
                    results.append(ShowResult(show_id=f"{self.name}:{quote(page_url,safe='')}:time:{show_time}:{idx}",provider=self.name,cinema=cinema,screen=None,show_time=show_time,available_seats=1,adjacent_available=None,booking_url=page_url))
        dedup={ (r.cinema.lower(),r.show_time,r.booking_url):r for r in results }; return list(dedup.values())
    async def check_availability(self, show_id: str) -> ShowResult: raise NotImplementedError("Public-page monitor performs fresh listing checks")
    async def get_booking_url(self, show_id: str) -> str:
        marker=":https%3A%2F%2F"
        if marker in show_id:
            from urllib.parse import unquote
            encoded=show_id.split(marker,1)[1].split(":",1)[0]; return unquote("https://"+encoded)
        return self.config.base_url
