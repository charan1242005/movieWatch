from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel
from typing import Optional
from app.providers.mock_provider import MockTicketProvider, force_state, reset_simulation
from app.providers.public_page_provider import PublicPageProvider
from app.schemas.movie import MovieOut
from app.utils.deps import get_current_user

router = APIRouter(prefix="/api", tags=["movies"])
_mock = MockTicketProvider()

@router.get("/movies/search")
async def search_movies(q: str = Query(..., min_length=1), city: str = Query(""), platform: str = Query("bookmyshow")):
    provider = _mock if platform == "mock" else PublicPageProvider(platform if platform in ("bookmyshow", "district") else "bookmyshow")
    results = await provider.search_movies(q, city)
    return [MovieOut(id=0, title=r.title, external_id=r.external_id, language=r.language, poster_url=r.poster_url) for r in results]

class ForceStateRequest(BaseModel):
    movie_id: str
    city: str
    date: str
    state: Optional[str] = None

@router.post("/dev/mock/force-state", tags=["dev"])
async def force_mock_state(payload: ForceStateRequest, current_user=Depends(get_current_user)):
    force_state(payload.movie_id, payload.city, payload.date, payload.state)
    return {"ok": True, "movie_id": payload.movie_id, "city": payload.city, "date": payload.date, "state": payload.state}

@router.post("/dev/mock/reset", tags=["dev"])
async def reset_mock_state(payload: ForceStateRequest, current_user=Depends(get_current_user)):
    reset_simulation(payload.movie_id, payload.city, payload.date)
    return {"ok": True}
