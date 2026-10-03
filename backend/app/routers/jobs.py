"""Job listing endpoints.

`/fetch` menarik lowongan live dari sumber (JobStreet, Glints) dan
mengembalikannya ternormalisasi. DB + scheduler menyusul di Fase berikutnya.
"""
from fastapi import APIRouter, Query

from app.fetchers.glints import GlintsFetcher
from app.fetchers.jobstreet import JobStreetFetcher

router = APIRouter()

FETCHERS = {
    "jobstreet": JobStreetFetcher(),
    "glints": GlintsFetcher(),
}


def _job_to_dict(job) -> dict:
    return {
        "id": job.id,
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
        "skills": job.skills,
        "url": job.url,
        "posted_at": job.posted_at,
    }


@router.get("")
async def list_jobs(
    source: str | None = Query(None, description="jobstreet | glints (kosong = semua)"),
    keywords: str = Query("backend engineer"),
    location: str = Query(""),
) -> dict:
    sources = [source] if source else list(FETCHERS)
    results: list[dict] = []
    for src in sources:
        fetcher = FETCHERS.get(src)
        if not fetcher:
            continue
        jobs = fetcher.fetch(keywords.split(), location=location)
        results.extend(_job_to_dict(j) for j in jobs)
    return {"count": len(results), "keywords": keywords, "jobs": results}
