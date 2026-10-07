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
from app.preferences import from_dict, passes_hard_filters, preference_boost, sort_results
from app.scheduler import collect_jobs
from app.store import get_jobs, save_cv

router = APIRouter()


def build_target(profile: CVProfile, preference: str, embedder, pref_weight: float):
    """Bangun target pencarian = gabungan CV + preferensi.

    Return (target_vec, target_skills, target_text, pref_tokens).
    - Tanpa preferensi: identik dengan CV, pref_tokens kosong.
    - Dengan preferensi: vektor di-blend, skill preferensi ditambahkan, teks
      disertakan, dan `pref_tokens` (kata kunci preferensi + skill-nya) dipakai
      untuk BOOST leksikal tegas saat scoring.
    """
    cv_vec = embedder.embed_one(profile.embedding_text)
    skills = list(profile.skills)
    text = profile.embedding_text
    pref_tokens: list[str] = []

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
        # Kumpulkan token preferensi bermakna untuk boost leksikal.
        pref_tokens = _pref_keywords(preference, pref_skills)

    return cv_vec, skills, text, pref_tokens


def _pref_keywords(preference: str, pref_skills: list[str]) -> list[str]:
    """Token kunci dari preferensi: skill terdeteksi + kata penting (>2 huruf)."""
    from app.matching.scorer import _tokens

    tokens = set(t.lower() for t in _tokens(preference))
    for s in pref_skills:
        tokens.add(s.lower())
    # Buang kata generik agar boost tidak kena semua lowongan.
    generic = {"engineer", "developer", "position", "role", "job", "kerja",
               "posisi", "bidang", "yang", "mau", "ingin", "saya", "di", "dan",
               "experience", "senior", "junior", "staff"}
    return [t for t in tokens if t not in generic and len(t) > 2]


def _pref_boost(job, jtext: str, jskills: list[str], pref_tokens: list[str]) -> float:
    """Boost tegas bila lowongan menyebut kata kunci preferensi.

    Hitung berapa token preferensi yang muncul di judul/skill/deskripsi lowongan.
    Tiap kemunculan menambah bobot, sehingga lowongan yang memang sesuai
    preferensi (mis. IoT) naik jauh di atas yang tidak.
    """
    if not pref_tokens:
        return 0.0
    hay = f"{job.title} {' '.join(jskills)} {jtext}".lower()
    hits = sum(1 for t in pref_tokens if t in hay)
    # 0 hit = 0; tiap hit menambah 0.08, maksimal 0.30 (agar tidak meledak).
    return min(0.30, 0.08 * hits)


def score_rows(rows: list, target_vec: list[float], target_skills: list[str],
               target_text: str, embedder, pref_tokens: list[str] | None = None,
               filters=None) -> list[dict]:
    """Skor semua baris lowongan terhadap target + boost preferensi + alasan.

    Kembalikan list (TIDAK diurutkan) — pengurutan diserahkan ke pemanggil
    (relevance / latest / salary / match_score via `sort_results`).
    """
    pref_tokens = pref_tokens or []
    filters = filters or from_dict(None)
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
        # Boost leksikal preferensi (tegas, bukan sekadar geser vektor).
        score = min(1.0, score + _pref_boost(row, jtext, jskills, pref_tokens))

        # Boost + alasan dari preferensi/filter lanjutan.
        pboost, preasons = preference_boost(row, filters)
        reasons: list[str] = preasons
        score = min(1.0, score + pboost)

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
                "reasons": reasons,
            }
        )
    return results


@router.post("")
def match_cv(
    file: UploadFile = File(...),
    keywords: str = Form(""),       # opsional — seed pengumpulan bila DB kosong
    location: str = Form(""),
    preference: str = Form(""),     # posisi/bidang yang diincar (mengemudikan matching)
    preference_weight: float = Form(0.65),  # 0..1, seberapa kuat preferensi vs CV
    filters: str = Form(""),        # JSON string preferensi/filter lanjutan
    source: str | None = Form(None),
    top_n: int = Form(30),
    user: User | None = Depends(get_optional_user),
) -> dict:
    preference_weight = max(0.0, min(1.0, preference_weight))

    # Parse filter lanjutan (JSON) → toleran terhadap payload kosong/rusak.
    import json
    try:
        filt = from_dict(json.loads(filters) if filters else None)
    except (json.JSONDecodeError, ValueError):
        filt = from_dict(None)

    # 1. Ekstrak CV → profil.
    content = file.file.read()
    text = extract_text(content, file.filename or "")
    profile = build_profile(text)
    embedder = get_embedder()

    # 2. Bangun target pencarian (CV + preferensi).
    target_vec, target_skills, target_text, pref_tokens = build_target(
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

    # 3b. Terapkan HARD FILTER (lokasi/tipe/gaji/pendidikan/perusahaan/remote).
    before_filter = len(rows)
    rows = [r for r in rows if passes_hard_filters(r, filt)]
    filtered_out = before_filter - len(rows)

    # 4. Skor semua lowongan terhadap target (termasuk boost preferensi).
    results = score_rows(rows, target_vec, target_skills, target_text, embedder, pref_tokens, filt)

    # 5. Urutkan sesuai preferensi; diversifikasi hanya untuk "relevance".
    results = sort_results(results, filt.sort_by)
    if filt.sort_by in ("", "relevance"):
        results = _diversify(results, top_n)
    else:
        results = results[:top_n]

    resp = profile.to_dict()
    resp["preference"] = preference.strip()
    resp["preference_weight"] = preference_weight
    resp["target_skills"] = target_skills
    return {
        "profile": resp,
        "count": len(results),
        "pool_size": len(rows),
        "filtered_out": filtered_out,
        "keywords": keywords,
        "filters_applied": {
            "sort_by": filt.sort_by,
            "hard_filters": [k for k in (
                "locations", "job_types", "min_salary", "max_salary",
                "education_levels", "excluded_companies", "remote", "hybrid",
            ) if getattr(filt, k)],
        },
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
