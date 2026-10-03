"""Penyimpanan job & CV ke database (dedupe/upsert)."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.db import SessionLocal
from app.fetchers.base import Job as JobData
from app.models import CVProfile, Job

# Kolom yang di-update saat terjadi konflik (source+external_id sudah ada).
_UPSERT_UPDATE_COLS = [
    "title", "company", "location", "salary_min", "salary_max", "currency",
    "job_type", "work_arrangement", "description", "requirements", "skills",
    "url", "posted_at", "embedding",
]


def _job_row(j: JobData, vec: list[float] | None) -> dict:
    return {
        "source": j.source,
        "external_id": j.external_id,
        "title": j.title,
        "company": j.company,
        "location": j.location,
        "salary_min": j.salary_min,
        "salary_max": j.salary_max,
        "currency": j.currency,
        "job_type": j.job_type,
        "work_arrangement": j.work_arrangement,
        "description": j.description,
        "requirements": j.requirements,
        "skills": j.skills,
        "url": j.url,
        "posted_at": j.posted_at,
        "embedding": vec,
    }


def upsert_jobs(jobs: list[JobData], embeddings: list[list[float]] | None = None) -> dict:
    """Upsert lowongan (dedupe by source+external_id). Return statistik.

    - Dedupe dalam satu batch (dict keyed source+external_id).
    - Upsert atomik (ON CONFLICT DO UPDATE) supaya aman dari duplikat lintas
      batch maupun dalam batch yang sama.
    """
    seen: dict[tuple[str, str], dict] = {}
    for i, j in enumerate(jobs):
        vec = embeddings[i] if embeddings else None
        key = (j.source, j.external_id)
        seen[key] = _job_row(j, vec)

    if not seen:
        return {"added": 0, "updated": 0, "total": 0}

    with SessionLocal() as db:
        # Pisahkan mana yang baru vs sudah ada, untuk statistik.
        keys = list(seen)
        existing_rows = db.execute(
            select(Job.source, Job.external_id).where(
                Job.source.in_([k[0] for k in keys]),
            )
        ).all()
        existing_pairs = {(s, e) for (s, e) in existing_rows}

        added = sum(1 for k in keys if k not in existing_pairs)
        updated = len(keys) - added

        stmt = sqlite_insert(Job).values(list(seen.values()))
        stmt = stmt.on_conflict_do_update(
            index_elements=["source", "external_id"],
            set_={c: getattr(stmt.excluded, c) for c in _UPSERT_UPDATE_COLS},
        )
        db.execute(stmt)
        db.commit()

    return {"added": added, "updated": updated, "total": len(seen)}


def get_jobs(limit: int = 500) -> list[Job]:
    with SessionLocal() as db:
        return list(db.scalars(select(Job).order_by(Job.id.desc()).limit(limit)))


def save_cv(filename: str, raw_text: str, skills: list[str], embedding: list[float] | None) -> CVProfile:
    with SessionLocal() as db:
        cv = CVProfile(filename=filename, raw_text=raw_text, skills=skills, embedding=embedding)
        db.add(cv)
        db.commit()
        db.refresh(cv)
        return cv


def get_latest_cv() -> CVProfile | None:
    with SessionLocal() as db:
        return db.scalars(select(CVProfile).order_by(CVProfile.id.desc())).first()
