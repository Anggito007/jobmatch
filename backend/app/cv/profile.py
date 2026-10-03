"""Ekstraksi profil terstruktur dari teks CV.

Untuk MVP: ambil skills (dari vocabulary) + teks mentah untuk embedding.
Nanti bisa ditambah parsing pengalaman/pendidikan.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.matching.skills import extract_skills


@dataclass
class CVProfile:
    raw_text: str
    skills: list[str]

    @property
    def embedding_text(self) -> str:
        """Teks yang di-embed — gabungkan semuanya."""
        skill_line = " ".join(self.skills)
        return f"{self.raw_text} {skill_line}".strip()


def build_profile(text: str) -> CVProfile:
    return CVProfile(raw_text=text, skills=extract_skills(text))
