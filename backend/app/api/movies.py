from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel
from typing import Optional

from app.providers.mock_provider import MockTicketProvider, force_state, reset_simulation
from app.schemas.movie import MovieOut
from app.utils.deps import get_current_user

router = APIRouter(prefix="/api", tags=["movies"])
_mock = MockTicketProvider()


@router.get("/movies/search")
async def search_movies(q: str = Query(..., min_length=1), city: str = Query("")):
    results = await _mock.search_movies(q, city)
    return [MovieOut(id=0, title=r.title, external_id=r.external_id,
                      language=r.language, poster_url=r.poster_url) for r in results]


class ForceStateRequest(BaseModel):
    movie_id: str
    city: str
    date: str
    state: Optional[str] = None  # one of MockState values, or null to clear


@router.post("/dev/mock/force-state", tags=["dev"])
async def force_mock_state(payload: ForceStateRequest, current_user=Depends(get_current_user)):
    """
    Developer/admin endpoint to instantly force the mock provider's simulated
    state for a given (movie_id, city, date) showset:
    MOVIE_NOT_AVAILABLE | SHOW_NOT_AVAILABLE | SHOW_AVAILABLE | SEATS_AVAILABLE | SEATS_SOLD_OUT
    """
    force_state(payload.movie_id, payload.city, payload.date, payload.state)
    return {"ok": True, "movie_id": payload.movie_id, "city": payload.city,
            "date": payload.date, "state": payload.state}


@router.post("/dev/mock/reset", tags=["dev"])
async def reset_mock_state(payload: ForceStateRequest, current_user=Depends(get_current_user)):
    reset_simulation(payload.movie_id, payload.city, payload.date)
    return {"ok": True}
