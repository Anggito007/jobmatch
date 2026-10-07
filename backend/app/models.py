"""SQLAlchemy models."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Job(Base):
    """Lowongan tersimpan (dedupe by source+external_id)."""

    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("source", "external_id", name="uq_job_source_ext"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(32), index=True)
    external_id: Mapped[str] = mapped_column(String(64))

    title: Mapped[str] = mapped_column(String(255), index=True)
    company: Mapped[str] = mapped_column(String(255), default="")
    location: Mapped[str] = mapped_column(String(255), default="")
    salary_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    salary_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(8), default="IDR")
    job_type: Mapped[str] = mapped_column(String(64), default="")
    work_arrangement: Mapped[str] = mapped_column(String(64), default="")

    description: Mapped[str] = mapped_column(Text, default="")
    requirements: Mapped[str] = mapped_column(Text, default="")
    skills: Mapped[list] = mapped_column(JSON, default=list)

    url: Mapped[str] = mapped_column(String(512), default="")
    posted_at: Mapped[str] = mapped_column(String(64), default="")

    # Embedding lowongan (list float) — disimpan sebagai JSON.
    # Di produksi (pgvector) ganti jadi kolom vektor.
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)

    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class User(Base):
    """Akun pengguna (auth)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class AuthSession(Base):
    """Sesi login (opaque token)."""

    __tablename__ = "auth_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime)


class Feedback(Base):
    """Feedback relevansi lowongan (👍/👎) — bahan data untuk reranker kelak."""

    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    job_source: Mapped[str] = mapped_column(String(32))
    job_external_id: Mapped[str] = mapped_column(String(64))
    is_relevant: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class SavedJob(Base):
    """Lowongan yang disimpan/ditandai status lamaran user."""

    __tablename__ = "saved_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    job_source: Mapped[str] = mapped_column(String(32))
    job_external_id: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16), default="saved")  # saved | applied
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class UserPreferences(Base):
    """Preferensi/filter pencarian lowongan per user (persisten)."""

    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)

    locations: Mapped[list] = mapped_column(JSON, default=list)
    position_levels: Mapped[list] = mapped_column(JSON, default=list)
    job_types: Mapped[list] = mapped_column(JSON, default=list)
    specializations: Mapped[list] = mapped_column(JSON, default=list)
    education_levels: Mapped[list] = mapped_column(JSON, default=list)
    preferred_companies: Mapped[list] = mapped_column(JSON, default=list)
    excluded_companies: Mapped[list] = mapped_column(JSON, default=list)

    min_salary: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_salary: Mapped[float | None] = mapped_column(Float, nullable=True)
    salary_currency: Mapped[str] = mapped_column(String(8), default="")
    salary_not_specified: Mapped[bool] = mapped_column(Boolean, default=False)

    remote: Mapped[bool] = mapped_column(Boolean, default=False)
    hybrid: Mapped[bool] = mapped_column(Boolean, default=False)
    work_abroad: Mapped[bool] = mapped_column(Boolean, default=False)
    fresh_graduate: Mapped[bool] = mapped_column(Boolean, default=False)
    quick_response: Mapped[bool] = mapped_column(Boolean, default=False)

    sort_by: Mapped[str] = mapped_column(String(32), default="relevance")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class CVProfile(Base):
    """CV pengguna (untuk MVP: 1 CV aktif per user, yang terbaru menang)."""

    __tablename__ = "cv_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    filename: Mapped[str] = mapped_column(String(255), default="")
    raw_text: Mapped[str] = mapped_column(Text, default="")
    skills: Mapped[list] = mapped_column(JSON, default=list)
    years_experience: Mapped[int | None] = mapped_column(Integer, nullable=True)
    education: Mapped[str] = mapped_column(String(64), default="")
    target_role: Mapped[str] = mapped_column(String(128), default="")
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
