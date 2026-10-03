"""Penyimpanan job & CV ke database (dedupe/upsert)."""
from __future__ import annotations

from sqlalchemy import select

from app.db import SessionLocal
from app.fetchers.base import Job as JobData
from app.models import CVProfile, Job


def upsert_jobs(jobs: list[JobData], embeddings: list[list[float]] | None = None) -> dict:
    """Upsert lowongan (dedupe by source+external_id). Return statistik.

    `embeddings` (opsional) sejajar dengan `jobs`; dipakai untuk mengisi
    kolom embedding agar matching tidak perlu re-embed saat request.
    """
    added = 0
    updated = 0
    with SessionLocal() as db:
        for i, j in enumerate(jobs):
            vec = embeddings[i] if embeddings else None
            row = db.scalar(
                select(Job).where(Job.source == j.source, Job.external_id == j.external_id)
            )
            if row:
                row.title = j.title
                row.company = j.company
                row.location = j.location
                row.salary_min = j.salary_min
                row.salary_max = j.salary_max
                row.currency = j.currency
                row.job_type = j.job_type
                row.work_arrangement = j.work_arrangement
                row.description = j.description
                row.requirements = j.requirements
                row.skills = j.skills
                row.url = j.url
                row.posted_at = j.posted_at
                if vec is not None:
                    row.embedding = vec
                updated += 1
            else:
                db.add(
                    Job(
                        source=j.source,
                        external_id=j.external_id,
                        title=j.title,
                        company=j.company,
                        location=j.location,
                        salary_min=j.salary_min,
                        salary_max=j.salary_max,
                        currency=j.currency,
                        job_type=j.job_type,
                        work_arrangement=j.work_arrangement,
                        description=j.description,
                        requirements=j.requirements,
                        skills=j.skills,
                        url=j.url,
                        posted_at=j.posted_at,
                        embedding=vec,
                    )
                )
                added += 1
        db.commit()
    return {"added": added, "updated": updated, "total": added + updated}


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
