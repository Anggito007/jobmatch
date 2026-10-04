"""Penyimpanan job & CV ke database (dedupe/upsert)."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.db import SessionLocal
from app.fetchers.base import Job as JobData
from app.models import CVProfile, Feedback, Job, SavedJob, User

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


def save_cv(
    filename: str,
    raw_text: str,
    skills: list[str],
    embedding: list[float] | None,
    user_id: int | None = None,
    years_experience: int | None = None,
    education: str = "",
    target_role: str = "",
) -> CVProfile:
    with SessionLocal() as db:
        cv = CVProfile(
            filename=filename,
            raw_text=raw_text,
            skills=skills,
            embedding=embedding,
            user_id=user_id,
            years_experience=years_experience,
            education=education,
            target_role=target_role,
        )
        db.add(cv)
        db.commit()
        db.refresh(cv)
        return cv


def get_latest_cv(user_id: int | None = None) -> CVProfile | None:
    with SessionLocal() as db:
        q = select(CVProfile)
        if user_id is None:
            q = q.where(CVProfile.user_id.is_(None))
        else:
            q = q.where(CVProfile.user_id == user_id)
        return db.scalars(q.order_by(CVProfile.id.desc())).first()


# --- Auth ---

def create_user(email: str, password_hash: str) -> User | None:
    """Buat user baru; None bila email sudah terdaftar."""
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email == email)):
            return None
        u = User(email=email, password_hash=password_hash)
        db.add(u)
        db.commit()
        db.refresh(u)
        return u


def get_user_by_email(email: str) -> User | None:
    with SessionLocal() as db:
        return db.scalar(select(User).where(User.email == email))


# --- Feedback relevansi ---

def save_feedback(user_id: int, source: str, ext_id: str, is_relevant: bool) -> str:
    """Upsert feedback (satu per user per job)."""
    with SessionLocal() as db:
        row = db.scalar(
            select(Feedback).where(
                Feedback.user_id == user_id,
                Feedback.job_source == source,
                Feedback.job_external_id == ext_id,
            )
        )
        if row:
            row.is_relevant = is_relevant
            action = "updated"
        else:
            db.add(Feedback(user_id=user_id, job_source=source, job_external_id=ext_id, is_relevant=is_relevant))
            action = "created"
        db.commit()
        return action


# --- Lowongan tersimpan ---

def save_job(user_id: int, source: str, ext_id: str, status: str = "saved") -> str:
    """Upsert lowongan tersimpan (satu per user per job)."""
    with SessionLocal() as db:
        row = db.scalar(
            select(SavedJob).where(
                SavedJob.user_id == user_id,
                SavedJob.job_source == source,
                SavedJob.job_external_id == ext_id,
            )
        )
        if row:
            row.status = status
            action = "updated"
        else:
            db.add(SavedJob(user_id=user_id, job_source=source, job_external_id=ext_id, status=status))
            action = "created"
        db.commit()
        return action


def list_saved(user_id: int) -> list[dict]:
    with SessionLocal() as db:
        rows = db.scalars(
            select(SavedJob).where(SavedJob.user_id == user_id).order_by(SavedJob.id.desc())
        ).all()
        return [
            {
                "id": f"{r.job_source}:{r.job_external_id}",
                "source": r.job_source,
                "external_id": r.job_external_id,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else "",
            }
            for r in rows
        ]


def delete_saved(user_id: int, source: str, ext_id: str) -> bool:
    with SessionLocal() as db:
        row = db.scalar(
            select(SavedJob).where(
                SavedJob.user_id == user_id,
                SavedJob.job_source == source,
                SavedJob.job_external_id == ext_id,
            )
        )
        if row:
            db.delete(row)
            db.commit()
            return True
        return False
