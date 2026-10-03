"""SQLAlchemy models."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, Integer, String, Text, UniqueConstraint
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


class CVProfile(Base):
    """CV pengguna (untuk MVP: 1 CV, yang terbaru menang)."""

    __tablename__ = "cv_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), default="")
    raw_text: Mapped[str] = mapped_column(Text, default="")
    skills: Mapped[list] = mapped_column(JSON, default=list)
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
