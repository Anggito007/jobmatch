"""Endpoint matching: upload CV (+ preferensi target) → skor terhadap POOL.

Alur:
1. Ekstrak CV → profil → embedding.
2. (Baru) Bila ada `preference` (posisi/bidang yang diincar), embedding preferensi
   digabung dengan embedding CV (blend) — sehingga pencarian "dikemudikan" ke
   arah yang diinginkan user, bukan cuma mencerminkan skill CV. Skill preferensi
   juga ditambahkan ke set skill target.
3. Baca pool lowongan dari DB; bila kosong, kumpulkan broad dulu.
4. Skor semua lowongan (cosine + skill + lexical) terhadap TARGET gabungan.
5. Urutkan + diversifikasi, kembalikan top_n.

Catatan: endpoint `def` supaya encoding embedding (blocking) jalan di threadpool.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.auth import get_optional_user
from app.cv.extract import extract_text
from app.cv.profile import CVProfile, build_profile
from app.matching.embedder import get_embedder
from app.matching.scorer import blend_vectors, job_skills, job_text, score_match
from app.matching.skills import extract_skills
from app.models import User
from app.scheduler import collect_jobs
from app.store import get_jobs, save_cv

router = APIRouter()


def build_target(profile: CVProfile, preference: str, embedder, pref_weight: float):
    """Bangun target pencarian = gabungan CV + preferensi.

    Return (target_vec, target_skills, target_text).
    - Tanpa preferensi: identik dengan CV.
    - Dengan preferensi: vektor di-blend (preferensi dominan), skill preferensi
      ditambahkan, teks preferensi disertakan untuk sinyal leksikal.
    """
    cv_vec = embedder.embed_one(profile.embedding_text)
    skills = list(profile.skills)
    text = profile.embedding_text

    preference = (preference or "").strip()
    if preference:
        pref_vec = embedder.embed_one(preference)
        cv_vec = blend_vectors(cv_vec, pref_vec, pref_weight)
        pref_skills = extract_skills(preference)
        seen = {s.lower() for s in skills}
        for s in pref_skills:
            if s.lower() not in seen:
                seen.add(s.lower())
                skills.append(s)
        text = f"{text} {preference}"

    return cv_vec, skills, text


def score_rows(rows: list, target_vec: list[float], target_skills: list[str],
               target_text: str, embedder) -> list[dict]:
    """Skor semua baris lowongan terhadap target; kembalikan terurut skor menurun."""
    results: list[dict] = []
    for row in rows:
        jtext = job_text(row)
        jvec = row.embedding
        if not jvec:
            jvec = embedder.embed_one(jtext)
        jskills = row.skills or job_skills(row)
        score, matched = score_match(
            list(target_vec), list(jvec), target_skills, jskills,
            cv_text=target_text, job_text_str=jtext,
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
    preference: str = Form(""),     # posisi/bidang yang diincar (mengemudikan matching)
    preference_weight: float = Form(0.65),  # 0..1, seberapa kuat preferensi vs CV
    source: str | None = Form(None),
    top_n: int = Form(30),
    user: User | None = Depends(get_optional_user),
) -> dict:
    preference_weight = max(0.0, min(1.0, preference_weight))

    # 1. Ekstrak CV → profil.
    content = file.file.read()
    text = extract_text(content, file.filename or "")
    profile = build_profile(text)
    embedder = get_embedder()

    # 2. Bangun target pencarian (CV + preferensi).
    target_vec, target_skills, target_text = build_target(
        profile, preference, embedder, preference_weight
    )

    # 2b. Bila login, simpan profil CV ke akun (untuk digest & riwayat).
    if user is not None:
        save_cv(
            filename=file.filename or "",
            raw_text=text,
            skills=profile.skills,
            embedding=embedder.embed_one(profile.embedding_text),
            user_id=user.id,
            years_experience=profile.years_experience,
            education=profile.education,
            target_role=profile.target_role,
        )

    # 3. Ambil pool lowongan dari DB; kumpulkan broad bila kosong.
    rows = get_jobs(limit=5000)
    if source:
        rows = [r for r in rows if r.source == source]
    if not rows:
        kws = keywords.split() if keywords.strip() else []
        collect_jobs(keywords=kws)
        rows = get_jobs(limit=5000)
        if source:
            rows = [r for r in rows if r.source == source]

    # 4. Skor semua lowongan terhadap target.
    results = score_rows(rows, target_vec, target_skills, target_text, embedder)

    # 5. Diversifikasi + potong top_n.
    results = _diversify(results, top_n)

    resp = profile.to_dict()
    resp["preference"] = preference.strip()
    resp["preference_weight"] = preference_weight
    resp["target_skills"] = target_skills
    return {
        "profile": resp,
        "count": len(results),
        "pool_size": len(rows),
        "keywords": keywords,
        "matches": results,
    }


def _diversify(results: list[dict], top_n: int, max_per_company: int = 2, max_per_source: int = 8) -> list[dict]:
    """Re-rank untuk keberagaman: batasi tiap perusahaan & sumber."""
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
