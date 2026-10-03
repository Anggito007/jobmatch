"""Endpoint matching: upload CV → fetch lowongan → embed → score → urutkan.

Catatan: endpoint dibuat `def` (bukan `async def`) supaya FastAPI menjalankan
encoding embedding (blocking, sentence-transformers) di threadpool, tidak
memblokir event loop.
"""
from __future__ import annotations

from fastapi import APIRouter, File, Form, UploadFile

from app.cv.extract import extract_text
from app.cv.profile import build_profile
from app.fetchers.glints import GlintsFetcher
from app.fetchers.jobstreet import JobStreetFetcher
from app.matching.embedder import get_embedder
from app.matching.scorer import job_skills, job_text, score_match

router = APIRouter()

FETCHERS = {
    "jobstreet": JobStreetFetcher(),
    "glints": GlintsFetcher(),
}


@router.post("")
def match_cv(
    file: UploadFile = File(...),
    keywords: str = Form("backend engineer"),
    location: str = Form(""),
    source: str | None = Form(None),
    top_n: int = Form(20),
) -> dict:
    # 1. Ekstrak CV → profil → embedding.
    content = file.file.read()
    text = extract_text(content, file.filename or "")
    profile = build_profile(text)
    embedder = get_embedder()
    cv_vec = embedder.embed_one(profile.embedding_text)

    # 2. Fetch lowongan dari sumber.
    sources = [source] if source else list(FETCHERS)
    jobs = []
    for src in sources:
        fetcher = FETCHERS.get(src)
        if fetcher:
            jobs.extend(fetcher.fetch(keywords.split(), location=location))

    # 3. Embed semua lowongan (batch) + skill.
    texts = [job_text(j) for j in jobs]
    vecs = embedder.encode(texts) if texts else []

    # 4. Score tiap lowongan.
    results: list[dict] = []
    for job, jvec in zip(jobs, vecs):
        jskills = job_skills(job)
        score, matched = score_match(cv_vec, jvec, profile.skills, jskills)
        results.append(
            {
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
                "description": job.description[:300],
                "url": job.url,
                "posted_at": job.posted_at,
                "score": round(score, 4),
                "matched_skills": matched,
            }
        )

    # 5. Urutkan menurun, potong ke top_n.
    results.sort(key=lambda r: r["score"], reverse=True)
    results = results[:top_n]

    return {
        "cv_skills": profile.skills,
        "count": len(results),
        "keywords": keywords,
        "matches": results,
    }
