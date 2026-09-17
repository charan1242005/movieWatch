from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app import models  # noqa: F401  (ensure models are registered on Base)
from app.api import auth, movies, trackers, shows, notifications
from app.workers.availability_worker import start_scheduler, shutdown_scheduler
from app.utils.logger import get_logger

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    start_scheduler()
    logger.info("MovieWatch backend started")
    yield
    shutdown_scheduler()
    logger.info("MovieWatch backend stopped")


app = FastAPI(title="MovieWatch API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(movies.router)
app.include_router(trackers.router)
app.include_router(shows.router)
app.include_router(notifications.router)


@app.get("/health")
def health():
    return {"status": "ok"}
