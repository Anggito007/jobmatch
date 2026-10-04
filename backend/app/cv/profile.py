"""Ekstraksi profil terstruktur dari teks CV.

Untuk MVP: skills (dari vocabulary) + teks mentah untuk embedding, PLUS
field terstruktur tambahan (tahun pengalaman, pendidikan, target role) yang
diekstrak berbasis aturan untuk ditampilkan di UI.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from app.matching.skills import extract_skills

# --- Pola ekstraksi ---
_YEARS_RE = re.compile(r"(\d{1,2})\s*(?:\+)?\s*(?:tahun|thn|th\b|years?|yrs?)", re.IGNORECASE)
_YEAR_RANGE_RE = re.compile(r"(20\d{2})\s*[-–—]\s*(20\d{2}|sekarang|present|now|saat ini)", re.IGNORECASE)
_EDU_LEVELS = [
    ("S3", "S3"),
    ("S2", "S2"),
    ("S1", "S1"),
    ("D4", "Diploma (D4)"),
    ("D3", "Diploma (D3)"),
    ("Diploma", "Diploma"),
    ("SMK", "SMK"),
    ("SMA", "SMA"),
]

_HEADLINE_SKIP = {
    "keahlian", "ringkasan", "pengalaman", "pendidikan", "kontak", "summary",
    "skills", "experience", "education", "contact", "posisi", "role", "profil",
    "profile", "about", "tentang",
}


@dataclass
class CVProfile:
    raw_text: str
    skills: list[str]
    years_experience: int | None = None
    education: str = ""
    target_role: str = ""

    @property
    def embedding_text(self) -> str:
        """Teks yang di-embed — gabungkan semuanya."""
        skill_line = " ".join(self.skills)
        return f"{self.raw_text} {skill_line}".strip()

    def to_dict(self) -> dict:
        return {
            "skills": self.skills,
            "years_experience": self.years_experience,
            "education": self.education,
            "target_role": self.target_role,
        }


def extract_years_experience(text: str) -> int | None:
    """Estimasi total tahun pengalaman.

    - Klaim eksplisit ("4 tahun", "5+ years") dihitung dari seluruh teks.
    - Rentang tahun dihitung HANYA dari bagian pengalaman (sebelum seksi
      pendidikan), supaya "(2016 - 2020)" pada pendidikan tidak ikut terhitung.
    """
    best: int | None = None

    # 1. Klaim eksplisit.
    for m in _YEARS_RE.finditer(text):
        n = int(m.group(1))
        if n > 30:  # anomali (mis. tahun 20xx terpotong)
            continue
        best = n if best is None or n > best else best

    # 2. Rentang tahun — hanya sampai garis "PENDIDIKAN / EDUCATION".
    exp_text = text
    edu_match = re.search(r"(?im)^\s*(pendidikan|education)\s*:?\s*$", text)
    if edu_match:
        exp_text = text[: edu_match.start()]

    total_years = 0
    current = datetime.now().year
    for m in _YEAR_RANGE_RE.finditer(exp_text):
        start = int(m.group(1))
        end_raw = m.group(2).lower()
        end = current if end_raw in ("sekarang", "present", "now", "saat ini") else int(end_raw)
        if end >= start:
            total_years += end - start

    if total_years > 0:
        best = total_years if best is None else max(best, total_years)

    return best


def extract_education(text: str) -> str:
    """Deteksi tingkat pendidikan tertinggi dari teks."""
    for keyword, label in _EDU_LEVELS:
        if re.search(rf"\b{re.escape(keyword)}\b", text, re.IGNORECASE):
            return label
    return ""


def extract_target_role(text: str) -> str:
    """Inferensi target role dari headline CV (baris pendek setelah nama)."""
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    for ln in lines[1:6]:
        low = ln.lower()
        if low in _HEADLINE_SKIP or any(k in low for k in _HEADLINE_SKIP):
            continue
        if "@" in ln or len(re.sub(r"\D", "", ln)) > 8:
            continue
        if len(ln) < 3 or len(ln) > 60:
            continue
        return ln
    return ""


def build_profile(text: str) -> CVProfile:
    return CVProfile(
        raw_text=text,
        skills=extract_skills(text),
        years_experience=extract_years_experience(text),
        education=extract_education(text),
        target_role=extract_target_role(text),
    )
