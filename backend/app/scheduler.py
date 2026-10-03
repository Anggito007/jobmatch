"""Scheduler — fetch berkala + embed + simpan, dan seeding awal.

Menggunakan APScheduler (BackgroundScheduler). `collect_jobs()` bisa dipanggil
manual (mis. endpoint `/api/jobs/refresh`) atau terjadwal.
"""
from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.fetchers.glints import GlintsFetcher
from app.fetchers.jobstreet import JobStreetFetcher
from app.matching.embedder import get_embedder
from app.matching.scorer import job_skills, job_text
from app.store import upsert_jobs

log = logging.getLogger("jobmatch.scheduler")

FETCHERS = {
    "jobstreet": JobStreetFetcher(),
    "glints": GlintsFetcher(),
}

_scheduler: BackgroundScheduler | None = None


def collect_jobs(keywords: list[str] | None = None, location: str = "") -> dict:
    """Fetch dari semua sumber, embed, simpan (dedupe)."""
    keywords = keywords or ["software engineer", "backend", "programmer"]
    total_added = 0
    total_updated = 0
    fetched = 0

    embedder = get_embedder()

    for name, fetcher in FETCHERS.items():
        try:
            jobs = fetcher.fetch(keywords, location=location)
        except Exception as e:  # satu sumber gagal tidak menghentikan lainnya
            log.warning("fetch %s gagal: %s", name, e)
            continue

        texts = [job_text(j) for j in jobs]
        vecs = embedder.encode(texts) if texts else []
        # Sertakan skill hasil ekstraksi di objek job sebelum disimpan.
        for job, text in zip(jobs, texts):
            job.skills = job_skills(job)
        stats = upsert_jobs(jobs, vecs)
        fetched += len(jobs)
        total_added += stats["added"]
        total_updated += stats["updated"]

    return {
        "fetched": fetched,
        "added": total_added,
        "updated": total_updated,
        "sources": list(FETCHERS),
    }


def start_scheduler(interval_hours: int = 6, keywords: list[str] | None = None) -> BackgroundScheduler:
    """Mulai scheduler background. Idempoten (tidak dobel)."""
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    _scheduler = BackgroundScheduler(timezone="Asia/Jakarta")
    _scheduler.add_job(
        collect_jobs,
        "interval",
        hours=interval_hours,
        kwargs={"keywords": keywords},
        id="collect_jobs",
        replace_existing=True,
    )
    _scheduler.start()
    log.info("Scheduler dimulai (tiap %s jam)", interval_hours)
    return _scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
