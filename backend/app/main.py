"""JobMatch backend — FastAPI entrypoint."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import init_db
from app.routers import cv, jobs, match
from app.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: buat tabel, jalankan scheduler (fetch berkala + dedupe).
    init_db()
    start_scheduler(interval_hours=settings.fetch_interval_hours)
    yield
    # Shutdown.
    stop_scheduler()


app = FastAPI(
    title="JobMatch API",
    description="Job seeker automation: CV matching + job tracking",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS untuk frontend Next.js (Vercel) saat development & production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cv.router, prefix="/api/cv", tags=["cv"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(match.router, prefix="/api/match", tags=["match"])


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok", "service": "jobmatch", "version": "0.1.0"}
