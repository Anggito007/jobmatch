"""Scoring — gabungkan cosine similarity embedding dengan overlap skill.

Skor akhir = 0.75 * cosine + 0.25 * skill_overlap (Jaccard).
Kedua komponen ternormalisasi 0..1.
"""
from __future__ import annotations

from .skills import extract_skills, skill_overlap_score

COSINE_WEIGHT = 0.75
SKILL_WEIGHT = 0.25


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity dua vektor (sudah dinormalisasi → cukup dot product)."""
    if not a or not b or len(a) != len(b):
        return 0.0
    return sum(x * y for x, y in zip(a, b))


def score_match(
    cv_vec: list[float],
    job_vec: list[float],
    cv_skills: list[str],
    job_skills: list[str],
) -> tuple[float, list[str]]:
    """Hitung skor kecocokan 0..1 + daftar skill yang tumpang-tindih.

    Returns:
        (score, matched_skills)
    """
    cos = cosine_similarity(cv_vec, job_vec)
    overlap = skill_overlap_score(cv_skills, job_skills)

    cv_set = {s.lower() for s in cv_skills}
    matched = [s for s in job_skills if s.lower() in cv_set]

    score = COSINE_WEIGHT * cos + SKILL_WEIGHT * overlap
    return score, matched


def job_text(job) -> str:
    """Gabungkan field lowongan jadi satu teks untuk embedding + skill."""
    parts = [
        job.title,
        job.company,
        job.description,
        job.requirements,
        job.job_type,
        job.work_arrangement,
    ]
    return " ".join(p for p in parts if p)


def job_skills(job) -> list[str]:
    """Ekstrak skill dari field lowongan."""
    return extract_skills(job_text(job))
