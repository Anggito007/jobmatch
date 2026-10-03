"""Job listing endpoints — baca dari DB (dipopulasi scheduler).

`POST /api/jobs/refresh` memicu pengumpulan lowongan segera (fetch + embed +
simpan). `GET /api/jobs` membaca yang sudah tersimpan.
"""
from fastapi import APIRouter, Query

from app.scheduler import collect_jobs
from app.store import get_jobs

router = APIRouter()


def _job_to_dict(job) -> dict:
    return {
        "id": f"{job.source}:{job.external_id}",
        "source": job.source,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "currency": job.currency,
        "job_type": job.job_type,
        "work_arrangement": job.work_arrangement,
        "description": job.description,
        "skills": job.skills or [],
        "url": job.url,
        "posted_at": job.posted_at,
    }


@router.get("")
async def list_jobs(
    source: str | None = Query(None, description="jobstreet | glints (kosong = semua)"),
    limit: int = Query(200, ge=1, le=1000),
) -> dict:
    rows = get_jobs(limit=limit)
    if source:
        rows = [r for r in rows if r.source == source]
    return {"count": len(rows), "jobs": [_job_to_dict(r) for r in rows]}


@router.post("/refresh")
async def refresh_jobs() -> dict:
    """Trigger pengumpulan lowongan sekarang (blocking, bisa lambat saat model belum dimuat)."""
    return collect_jobs()
