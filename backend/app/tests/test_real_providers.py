import pytest
from app.providers.bookmyshow_provider import BookMyShowProvider, _resolve_city, _parse_event_and_slug
from app.providers.district_provider import DistrictProvider, _resolve_district_city, _parse_district_id
from app.models.tracker import Tracker, Platform
from app.models.show import Show
from app.services.tracker_service import _time_in_range

def test_resolve_city():
    slug, code = _resolve_city('Visakhapatnam')
    assert slug == 'vizag-visakhapatnam'
    assert code == 'VIZA'

    slug, code = _resolve_city('Hyderabad')
    assert slug == 'hyderabad'
    assert code == 'HYD'

def test_parse_event_and_slug():
    code, slug = _parse_event_and_slug('ET00514261::mandaadi-telugu')
    assert code == 'ET00514261'
    assert slug == 'mandaadi-telugu'

    code, slug = _parse_event_and_slug('https://in.bookmyshow.com/buytickets/devara-part-1-hyderabad/movie-hyd-ET00310790-MT/20260925')
    assert code == 'ET00310790'

def test_district_city_resolve():
    assert _resolve_district_city('Visakhapatnam') == 'vizag'
    assert _resolve_district_city('Bengaluru') == 'bengaluru'

def test_multi_theatre_matching():
    filter_cinema = 'PVR CMR Central + INOX + Asian'
    targets = [t.strip().lower() for t in filter_cinema.replace('+', ',').replace('|', ',').split(',') if t.strip()]

    assert any(t in 'INOX: CMR Central, Maddilapalem'.lower() for t in targets)
    assert any(t in 'INOX: Varun Beach, Beach Road'.lower() for t in targets)
    assert any(t in 'Asian Mukta A2 Cinemas'.lower() for t in targets)
    assert not any(t in 'Jagadamba Complex'.lower() for t in targets)
