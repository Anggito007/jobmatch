"""Scheduler — fetch berkala + embed + simpan, dan seeding awal.

Menggunakan APScheduler (BackgroundScheduler). `collect_jobs()` bisa dipanggil
manual (mis. endpoint `/api/jobs/refresh`) atau terjadwal.

Dua mode pengumpulan:
- **broad** (keywords kosong) — feed terbaru tiap sumber, untuk mengisi pool.
- **targeted** (keywords diisi) — pencarian kata kunci nyata di tiap portal.
  Inilah yang membuat hasil banyak: portal mencari SELURUH indeksnya
  (JobStreet melaporkan 1.669 hasil untuk "video editor"), bukan hanya
  snapshot pool kita yang ~2.000 lowongan.

Fetch dijalankan PARALEL antar sumber (dulu berurutan → lambat).
"""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from apscheduler.schedulers.background import BackgroundScheduler

from app.fetchers.base import BaseFetcher, Job
from app.fetchers.dealls import DeallsFetcher
from app.fetchers.glints import GlintsFetcher
from app.fetchers.jobstreet import JobStreetFetcher
from app.fetchers.kalibrr import KalibrrFetcher
from app.fetchers.karir import KarirFetcher
from app.fetchers.techinasia import TechInAsiaFetcher
from app.matching.embedder import get_embedder
from app.matching.scorer import job_skills, job_text
from app.store import upsert_jobs

log = logging.getLogger("jobmatch.scheduler")

FETCHERS: dict[str, BaseFetcher] = {
    "jobstreet": JobStreetFetcher(),
    "glints": GlintsFetcher(),
    "dealls": DeallsFetcher(),
    "kalibrr": KalibrrFetcher(),
    "karir": KarirFetcher(),
    "techinasia": TechInAsiaFetcher(),
}

# Batas lowongan per sumber saat fetch. Tanpa ini Kalibrr (yang selalu
# mengembalikan ~1.400 lowongan) mendominasi pool sampai >60% dan hasil
# pencarian jadi berat sebelah ke satu situs.
PER_SOURCE_CAP = 400

_scheduler: BackgroundScheduler | None = None


def fetch_all(
    keywords: list[str] | None = None,
    location: str = "",
    per_source_cap: int = PER_SOURCE_CAP,
    max_workers: int = 6,
) -> tuple[list[Job], list[str]]:
    """Fetch dari semua sumber PARALEL. Return (jobs, sumber_yang_gagal).

    Gagal di satu sumber tidak menghentikan sumber lain (mis. Glints yang
    kadang balas 403 karena rate-limit).
    """
    keywords = keywords or []
    all_jobs: list[Job] = []
    failed: list[str] = []

    def _one(name: str, fetcher: BaseFetcher) -> tuple[str, list[Job]]:
        try:
            jobs = fetcher.fetch(keywords, location=location)
            if per_source_cap and len(jobs) > per_source_cap:
                jobs = jobs[:per_source_cap]
            return name, jobs
        except Exception as e:  # noqa: BLE001 — satu sumber gagal, lanjut
            log.warning("fetch %s gagal: %s", name, e)
            return name, []

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_one, n, f): n for n, f in FETCHERS.items()}
        for fut in as_completed(futures):
            name, jobs = fut.result()
            if not jobs:
                failed.append(name)
            all_jobs.extend(jobs)

    return all_jobs, failed


def _store(jobs: list[Job]) -> dict:
    """Embed + upsert daftar job. Return statistik."""
    if not jobs:
        return {"added": 0, "updated": 0}
    embedder = get_embedder()
    texts = [job_text(j) for j in jobs]
    vecs = embedder.encode(texts) if texts else []
    for job, text in zip(jobs, texts):
        job.skills = job_skills(job)
    stats = upsert_jobs(jobs, vecs)
    return {"added": stats["added"], "updated": stats["updated"]}


def collect_jobs(
    keywords: list[str] | None = None,
    location: str = "",
    per_source_cap: int = PER_SOURCE_CAP,
) -> dict:
    """Fetch dari semua sumber (paralel), embed, simpan (dedupe).

    `keywords` kosong = broad fetch (feed terbaru tiap sumber).
    """
    keywords = keywords or []
    jobs, failed = fetch_all(keywords, location=location, per_source_cap=per_source_cap)
    stats = _store(jobs)
    return {
        "fetched": len(jobs),
        "added": stats["added"],
        "updated": stats["updated"],
        "sources": list(FETCHERS),
        "failed_sources": failed,
    }


def collect_jobs_live(
    keywords: list[str],
    location: str = "",
    per_source_cap: int = PER_SOURCE_CAP,
) -> dict:
    """Fetch TERARAH dengan kata kunci user, lalu simpan.

    Dipakai sebelum matching supaya hasil mengikuti isi indeks portal
    (bukan hanya pool yang tersimpan). Return statistik + jumlah per sumber.
    """
    jobs, failed = fetch_all(keywords, location=location, per_source_cap=per_source_cap)
    stats = _store(jobs)

    per_source: dict[str, int] = {}
    for j in jobs:
        per_source[j.source] = per_source.get(j.source, 0) + 1

    return {
        "fetched": len(jobs),
        "added": stats["added"],
        "updated": stats["updated"],
        "per_source": per_source,
        "failed_sources": failed,
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
