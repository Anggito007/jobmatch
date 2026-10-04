"""Endpoint matching: upload CV → skor terhadap POOL lowongan tersimpan.

Alur (sesuai tujuan "semua loker yang sesuai CV"):
1. Ekstrak CV → embed.
2. Baca pool lowongan dari DB (dipopulasi scheduler, sudah di-embed).
   Jika DB kosong (first run), lakukan pengumpulan broad dulu.
3. Skor cosine + skill-overlap terhadap SEMUA lowongan pool (bukan keyword).
4. Urutkan, kembalikan top_n.

Catatan: endpoint `def` (bukan `async def`) supaya FastAPI menjalankan
encoding embedding (blocking) di threadpool.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.auth import get_optional_user
from app.cv.extract import extract_text
from app.cv.profile import CVProfile, build_profile
from app.matching.embedder import get_embedder
from app.matching.scorer import job_skills, job_text, score_match
from app.models import User
from app.scheduler import collect_jobs
from app.store import get_jobs, save_cv

router = APIRouter()


def score_rows(rows: list, profile: CVProfile, embedder, cv_vec: list[float]) -> list[dict]:
    """Skor semua baris lowongan terhadap CV; kembalikan terurut skor menurun."""
    results: list[dict] = []
    for row in rows:
        jtext = job_text(row)
        jvec = row.embedding
        if not jvec:
            jvec = embedder.embed_one(jtext)
        jskills = row.skills or job_skills(row)
        score, matched = score_match(
            cv_vec, list(jvec), profile.skills, jskills,
            cv_text=profile.embedding_text, job_text_str=jtext,
        )
        results.append(
            {
                "id": f"{row.source}:{row.external_id}",
                "source": row.source,
                "title": row.title,
                "company": row.company,
                "location": row.location,
                "salary_min": row.salary_min,
                "salary_max": row.salary_max,
                "currency": row.currency,
                "job_type": row.job_type,
                "work_arrangement": row.work_arrangement,
                "description": (row.description or "")[:300],
                "url": row.url,
                "posted_at": row.posted_at,
                "score": round(score, 4),
                "matched_skills": matched,
            }
        )
    results.sort(key=lambda r: r["score"], reverse=True)
    return results


@router.post("")
def match_cv(
    file: UploadFile = File(...),
    keywords: str = Form(""),       # opsional — seed pengumpulan bila DB kosong
    location: str = Form(""),
    source: str | None = Form(None),
    top_n: int = Form(30),
    user: User | None = Depends(get_optional_user),
) -> dict:
    # 1. Ekstrak CV → profil → embedding.
    content = file.file.read()
    text = extract_text(content, file.filename or "")
    profile = build_profile(text)
    embedder = get_embedder()
    cv_vec = embedder.embed_one(profile.embedding_text)

    # 1b. Bila login, simpan profil CV ke akun (untuk digest & riwayat).
    if user is not None:
        save_cv(
            filename=file.filename or "",
            raw_text=text,
            skills=profile.skills,
            embedding=cv_vec,
            user_id=user.id,
            years_experience=profile.years_experience,
            education=profile.education,
            target_role=profile.target_role,
        )

    # 2. Ambil pool lowongan dari DB (semua sumber, sudah di-embed scheduler).
    rows = get_jobs(limit=5000)
    if source:
        rows = [r for r in rows if r.source == source]
    if not rows:
        # First run: kumpulkan broad dulu, lalu baca ulang.
        kws = keywords.split() if keywords.strip() else []
        collect_jobs(keywords=kws)
        rows = get_jobs(limit=5000)
        if source:
            rows = [r for r in rows if r.source == source]

    # 3. Skor semua lowongan pool.
    results = score_rows(rows, profile, embedder, cv_vec)

    # 4. Diversifikasi (batasi dominasi satu perusahaan/sumber), potong top_n.
    results = _diversify(results, top_n)

    return {
        "profile": profile.to_dict(),
        "count": len(results),
        "pool_size": len(rows),
        "keywords": keywords,
        "matches": results,
    }


def _diversify(results: list[dict], top_n: int, max_per_company: int = 2, max_per_source: int = 8) -> list[dict]:
    """Re-rank untuk keberagaman: batasi tiap perusahaan & sumber.

    Iterasi greedy: ambil yang skor tertinggi, tapi lewati yang sudah melampaui
    kuota per-perusahaan / per-sumber, sampai terkumpul `top_n` atau habis.
    """
    out: list[dict] = []
    company_count: dict[str, int] = {}
    source_count: dict[str, int] = {}
    for r in results:
        company = r["company"] or "(unknown)"
        src = r["source"]
        if company_count.get(company, 0) >= max_per_company:
            continue
        if source_count.get(src, 0) >= max_per_source:
            continue
        company_count[company] = company_count.get(company, 0) + 1
        source_count[src] = source_count.get(src, 0) + 1
        out.append(r)
        if len(out) >= top_n:
            break
    return out
