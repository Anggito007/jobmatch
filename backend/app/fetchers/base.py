"""Antarmuka seragam untuk semua fetcher lowongan.

Setiap sumber (JobStreet, Glints, LinkedIn, ...) diimplementasikan sebagai
kelas yang mewarisi BaseFetcher dan mengembalikan list[Job]. Normalisasi ke
schema tunggal dilakukan DI DALAM masing-masing fetcher.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Job:
    """Schema tunggal untuk lowongan dari semua sumber."""

    source: str
    external_id: str
    title: str
    company: str = ""
    location: str = ""
    salary_min: float | None = None
    salary_max: float | None = None
    currency: str = "IDR"
    job_type: str = ""
    work_arrangement: str = ""
    description: str = ""
    requirements: str = ""
    skills: list[str] = field(default_factory=list)
    url: str = ""
    posted_at: str = ""
    fetched_at: str = ""

    @property
    def id(self) -> str:
        return f"{self.source}:{self.external_id}"


class BaseFetcher(ABC):
    """Interface wajib tiap fetcher sumber."""

    source_name: str = "base"

    @abstractmethod
    def fetch(self, keywords: list[str], location: str = "") -> list[Job]:
        """Ambil lowongan untuk kata kunci tertentu, sudah ternormalisasi."""
        raise NotImplementedError
