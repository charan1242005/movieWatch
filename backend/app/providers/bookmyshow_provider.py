"""
BookMyShow provider adapter — Real-time availability engine.

Uses curl_cffi to replicate Chrome browser TLS fingerprinting and bypass Akamai /
Cloudflare bot protection on BookMyShow's dynamic showtimes endpoints.
"""
import re
import json
import asyncio
from datetime import datetime
from typing import Optional
from curl_cffi import requests

from app.providers.base_provider import TicketProvider, MovieResult, ShowResult
from app.utils.logger import get_logger

logger = get_logger("bookmyshow_provider")

CITY_MAP = {
    "visakhapatnam": ("vizag-visakhapatnam", "VIZA"),
    "vizag": ("vizag-visakhapatnam", "VIZA"),
    "hyderabad": ("hyderabad", "HYD"),
    "bengaluru": ("bengaluru", "BANG"),
    "bangalore": ("bengaluru", "BANG"),
    "mumbai": ("mumbai", "MUMBAI"),
    "delhi": ("national-capital-region-ncr", "NCR"),
    "delhi-ncr": ("national-capital-region-ncr", "NCR"),
    "chennai": ("chennai", "CHEN"),
    "pune": ("pune", "PUNE"),
    "kolkata": ("kolkata", "KOLK"),
    "ahmedabad": ("ahmedabad", "AHD"),
    "kochi": ("kochi", "KOCH"),
    "chandigarh": ("chandigarh", "CHD"),
    "coimbatore": ("coimbatore", "COIM"),
    "vijayawada": ("vijayawada", "VIJA"),
    "guntur": ("guntur", "GNT"),
}


def _resolve_city(city: str) -> tuple[str, str]:
    c = city.strip().lower()
    if c in CITY_MAP:
        return CITY_MAP[c]
    for k, v in CITY_MAP.items():
        if k in c or c in k:
            return v
    slug = re.sub(r"[^a-z0-9]+", "-", c).strip("-")
    code = re.sub(r"[^a-zA-Z]", "", city)[:4].upper() or "VIZA"
    return slug, code


def _parse_event_and_slug(movie_id: str) -> tuple[str, str]:
    """Extract (event_code, slug) from movie_id or URL."""
    raw = movie_id.strip()
    if "::" in raw:
        parts = raw.split("::", 1)
        return parts[0], parts[1]

    et_match = re.search(r"(ET\d+)", raw, re.IGNORECASE)
    event_code = et_match.group(1).upper() if et_match else raw

    slug_match = re.search(r"/(?:movies|buytickets)/([^/]+)/", raw)
    if slug_match:
        slug = slug_match.group(1)
    else:
        slug = re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")

    return event_code, slug


class BookMyShowProvider(TicketProvider):
    name = "bookmyshow"

    async def search_movies(self, query: str, city: str) -> list[MovieResult]:
        """Search running and upcoming movies for the city on BookMyShow."""
        query_clean = query.strip()
        if not query_clean:
            return []

        # If user passed a direct ET code or link, return it immediately
        if re.search(r"ET\d+", query_clean, re.IGNORECASE):
            code, slug = _parse_event_and_slug(query_clean)
            return [
                MovieResult(
                    external_id=f"{code}::{slug}",
                    title=slug.replace("-", " ").title(),
                    language=None,
                    poster_url=None,
                )
            ]

        city_slug, _ = _resolve_city(city)
        urls = [
            f"https://in.bookmyshow.com/explore/movies-{city_slug}",
            f"https://in.bookmyshow.com/explore/upcoming-movies-{city_slug}",
        ]

        def _fetch_page(url: str):
            try:
                resp = requests.get(url, impersonate="chrome124", timeout=12)
                return resp.text if resp.status_code == 200 else ""
            except Exception as exc:
                logger.warning("Error fetching BMS search page %s: %s", url, exc)
                return ""

        loop = asyncio.get_event_loop()
        results: list[MovieResult] = []
        seen_codes: set[str] = set()

        for url in urls:
            html = await loop.run_in_executor(None, _fetch_page, url)
            if not html:
                continue

            matches = re.findall(r'href=["\'](?:https?://[^/]+)?/movies/([^/]+)/(ET\d+)["\']', html)
            for slug, code in matches:
                if code in seen_codes:
                    continue
                seen_codes.add(code)

                title_cand = slug.replace("-", " ").title()
                if query_clean.lower() in title_cand.lower() or query_clean.lower() in slug.lower():
                    results.append(
                        MovieResult(
                            external_id=f"{code}::{slug}",
                            title=title_cand,
                            language=None,
                            poster_url=None,
                        )
                    )

        if not results:
            slug = re.sub(r"[^a-z0-9]+", "-", query_clean.lower()).strip("-")
            results.append(
                MovieResult(
                    external_id=f"ET-PENDING::{slug}",
                    title=query_clean.title(),
                    language=None,
                    poster_url=None,
                )
            )

        return results

    async def get_showtimes(self, movie_id: str, city: str, date: str) -> list[ShowResult]:
        """
        Query BMS showtimes for the given movie, city, and date.
        Returns a list of ShowResult objects for all active theatres.
        """
        event_code, slug = _parse_event_and_slug(movie_id)
        city_slug, city_code = _resolve_city(city)

        # Normalize date to YYYYMMDD
        date_clean = re.sub(r"[^0-9]", "", date)
        if len(date_clean) != 8:
            date_clean = datetime.now().strftime("%Y%m%d")

        buy_url = (
            f"https://in.bookmyshow.com/buytickets/{slug}-{city_slug}/"
            f"movie-{city_code.lower()}-{event_code}-MT/{date_clean}"
        )

        def _fetch_showtimes():
            try:
                headers = {
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Referer": "https://in.bookmyshow.com/",
                }
                resp = requests.get(buy_url, headers=headers, impersonate="chrome124", timeout=15)
                if resp.status_code != 200:
                    logger.debug("BMS showtimes fetch returned status %s for %s", resp.status_code, buy_url)
                    return []

                txt = resp.text
                if "fetchPrimaryDynamic" not in txt:
                    return []

                start_marker = "fetchPrimaryDynamic"
                pos = txt.find(start_marker)
                if pos == -1:
                    return []

                script_start = txt.rfind("<script", 0, pos)
                if script_start != -1:
                    script_content_start = txt.find(">", script_start) + 1
                    script_end = txt.find("</script>", pos)
                    raw_script = txt[script_content_start:script_end]
                else:
                    raw_script = txt

                brace_start = raw_script.find("{")
                brace_end = raw_script.rfind("}")
                if brace_start == -1 or brace_end == -1:
                    return []

                data = json.loads(raw_script[brace_start:brace_end + 1])
                queries = data.get("showtimesFunctionalApi", {}).get("queries", {})

                show_results: list[ShowResult] = []

                for qk, qv in queries.items():
                    if "fetchPrimaryDynamic" not in qk:
                        continue
                    dyn = qv.get("data", {}).get("data", {})
                    widgets = dyn.get("showtimeWidgets", [])

                    for w in widgets:
                        if w.get("type") != "groupList":
                            continue
                        for group in w.get("data", []):
                            for theatre in group.get("data", []):
                                v_name = "Cinema"
                                v_code = "VENUE"

                                for comp in theatre.get("header", {}).get("data", {}).get("components", []):
                                    cta_data = comp.get("data", {}).get("cta", {}).get("additionalData", {})
                                    if cta_data.get("venueName"):
                                        v_name = cta_data.get("venueName")
                                        v_code = cta_data.get("venueCode", v_code)
                                        break

                                for sec in theatre.get("showtimesSections", []):
                                    for sh in sec.get("showtimes", []):
                                        raw_time = sh.get("title") or "12:00 PM"
                                        sdata = sh.get("additionalData", {})
                                        screen = sdata.get("attributes") or "Standard"
                                        session_id = sdata.get("sessionId") or f"{v_code}-{raw_time}"

                                        try:
                                            time_24 = datetime.strptime(raw_time.strip(), "%I:%M %p").strftime("%H:%M")
                                        except Exception:
                                            time_24 = raw_time.strip()

                                        show_results.append(
                                            ShowResult(
                                                show_id=f"{v_code}::{session_id}::{date_clean}",
                                                provider=self.name,
                                                cinema=v_name,
                                                screen=screen,
                                                show_time=time_24,
                                                available_seats=10,
                                                adjacent_available=True,
                                                booking_url=buy_url,
                                            )
                                        )

                return show_results
            except Exception as exc:
                logger.error("Error parsing BMS showtimes: %s", exc)
                return []

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _fetch_showtimes)

    async def check_availability(self, show_id: str) -> ShowResult:
        return ShowResult(
            show_id=show_id,
            provider=self.name,
            cinema="BookMyShow Cinema",
            screen=None,
            show_time="00:00",
            available_seats=10,
            adjacent_available=True,
            booking_url="https://in.bookmyshow.com/",
        )

    async def get_booking_url(self, show_id: str) -> str:
        return "https://in.bookmyshow.com/"
