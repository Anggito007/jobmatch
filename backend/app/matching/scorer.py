"""Scoring — hybrid: cosine + skill overlap + lexical overlap.

Skor akhir = 0.45 * cosine + 0.30 * skill_overlap + 0.25 * lexical_overlap.
Semua komponen ternormalisasi 0..1.

Alasan: cosine multilingual (MiniLM) compressed & bising — butuh sinyal
leksikal (judul/kata kunci) supaya "Backend Engineer" naik di atas "IT Support".
"""
from __future__ import annotations

import re

from .skills import extract_skills, skill_overlap_score

COSINE_WEIGHT = 0.45
SKILL_WEIGHT = 0.30
LEXICAL_WEIGHT = 0.25

# Stopword umum (id/en) yang tidak informatif untuk overlap.
_STOPWORDS = {
    "dan", "yang", "di", "ke", "dari", "untuk", "dengan", "the", "a", "an",
    "of", "and", "or", "in", "on", "at", "to", "for", "with", "is", "are",
    "be", "will", "as", "by", "this", "that", "we", "you", "our", "their",
    "saya", "kami", "kita", "ini", "itu", "akan", "atau", "pada",
}

_TOKEN_RE = re.compile(r"[a-z0-9+#.]+")


def _tokens(text: str) -> set[str]:
    """Kembalikan set token huruf kecil yang bermakna."""
    if not text:
        return set()
    toks = _TOKEN_RE.findall(text.lower())
    return {t for t in toks if len(t) > 1 and t not in _STOPWORDS}


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity dua vektor (sudah dinormalisasi → cukup dot product)."""
    if not a or not b or len(a) != len(b):
        return 0.0
    return sum(x * y for x, y in zip(a, b))


def blend_vectors(a: list[float], b: list[float], weight_b: float) -> list[float]:
    """Gabungkan dua vektor ternormalisasi.

    result = (1 - weight_b) * a + weight_b * b, lalu dinormalisasi ulang.
    Dipakai untuk menggabungkan vektor CV ("siapa saya") dengan vektor
    preferensi/target posisi ("mau ke mana"), sehingga pencarian bisa
    dikemudikan ke arah yang diinginkan user walau beda dari skill CV.
    """
    import numpy as np

    va = np.asarray(a, dtype="float32")
    vb = np.asarray(b, dtype="float32")
    out = (1.0 - weight_b) * va + weight_b * vb
    n = float(np.linalg.norm(out))
    if n > 0:
        out = out / n
    return out.tolist()


def lexical_overlap(cv_tokens: set[str], job_tokens: set[str], title_tokens: set[str]) -> float:
    """Overlap leksikal (recall): berapa token CV yang muncul di job (judul 2x)."""
    if not cv_tokens:
        return 0.0
    weighted_job = set(job_tokens) | set(title_tokens)
    inter = cv_tokens & weighted_job
    if not inter:
        return 0.0
    return len(inter) / len(cv_tokens)


def score_match(
    cv_vec: list[float],
    job_vec: list[float],
    cv_skills: list[str],
    job_skills: list[str],
    cv_text: str = "",
    job_text_str: str = "",
) -> tuple[float, list[str]]:
    """Hitung skor kecocokan 0..1 + daftar skill yang tumpang-tindih.

    Returns:
        (score, matched_skills)
    """
    cos = cosine_similarity(cv_vec, job_vec)
    overlap = skill_overlap_score(cv_skills, job_skills)

    cv_set = {s.lower() for s in cv_skills}
    matched = [s for s in job_skills if s.lower() in cv_set]

    lex = 0.0
    if cv_text and job_text_str:
        cv_tokens = _tokens(cv_text)
        # judul = 60 karakter pertama (heuristik: teks job diawali judul).
        title = job_text_str[:60]
        lex = lexical_overlap(cv_tokens, _tokens(job_text_str), _tokens(title))

    score = COSINE_WEIGHT * cos + SKILL_WEIGHT * overlap + LEXICAL_WEIGHT * lex
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
