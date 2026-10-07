"""Preferensi / filter pencarian lowongan.

Memisahkan dua jenis aturan terhadap lowongan:

- **HARD FILTER** (`passes_hard_filters`) — lowongan yang gagal DIBUANG. Ini
  keputusan biner: lokasi (bila dibatasi), tipe kerja, gaji minimum, pendidikan
  yang dipersyaratkan (bila lebih tinggi dari pendidikan user), pengecualian
  perusahaan, dan pengaturan kerja (remote/hybrid) bila dipilih eksplisit.

- **SOFT PREFERENCE** (`preference_boost`) — lowongan tetap tampil, tapi yang
  cocok dapat BOOST skor + alasan ("kenapa cocok"). Ini spesialisasi, perusahaan
  pilihan, level posisi, gaji di atas minimum, fresh graduate, dll.

Desain modular: setiap dimensi filter = satu fungsi kecil, sehingga menambah
filter baru tinggal menambah fungsi + mendaftarkannya di dua agregator.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Nilai kanonik (disepakati frontend & backend)
# ---------------------------------------------------------------------------

POSITION_LEVELS = ["internship", "fresh_graduate", "entry", "junior", "mid", "senior", "manager"]
JOB_TYPES = ["full_time", "part_time", "contract", "internship", "freelance", "temporary"]
EDUCATION_LEVELS = ["high_school", "diploma", "bachelor", "master", "doctorate", "any"]
SORT_OPTIONS = ["relevance", "latest", "salary_desc", "salary_asc", "match_score"]
CURRENCIES = ["IDR", "USD", "SGD", "EUR", ""]

# Urutan jenjang pendidikan (untuk "pendidikan dipersyaratkan > pendidikan user").
_EDU_RANK = {"high_school": 0, "diploma": 1, "bachelor": 2, "master": 3, "doctorate": 4}

# Kata kunci deteksi tiap level posisi (dari judul + deskripsi).
_POSITION_KEYWORDS: dict[str, list[str]] = {
    "internship": ["intern", "internship", "magang", "co-op", "coop"],
    "fresh_graduate": ["fresh grad", "fresh graduate", "freshgrad", "lulusan baru",
                       "management trainee", "graduate program", "entry level", "entry-level"],
    "entry": ["entry", "staf", "staff"],
    "junior": ["junior", " jr ", "jr.", "associate"],
    "mid": ["mid level", "mid-level", "middle"],
    "senior": ["senior", " sr ", "sr.", "lead", "principal", "staff engineer"],
    "manager": ["manager", "manajer", "head of", "director", "vp ", "chief"],
}

# Kata kunci spesialisasi.
_SPEC_KEYWORDS: dict[str, list[str]] = {
    "software_engineering": ["software", "developer", "programmer", "backend", "frontend",
                             "fullstack", "full stack", "web developer", "mobile developer",
                             "pemrograman", "programmer"],
    "network_engineering": ["network", "jaringan", "noc", "networking", "infrastructure",
                            "infrastruktur", "sysadmin", "devops"],
    "it_support": ["it support", "helpdesk", "help desk", "technical support",
                   "desktop support", "it support"],
    "data_science": ["data science", "data scientist", "machine learning", "data analyst",
                     "data engineer", "analytics", "artificial intelligence", "ai engineer",
                     "big data"],
    "cybersecurity": ["security", "cyber", "keamanan", "pentest", "penetration",
                      "soc analyst", "infosec"],
    "ui_ux": ["ui/ux", "ui ", "ux ", "product design", "graphic design", "desain",
              "designer", "figma"],
    "marketing": ["marketing", "digital marketing", "seo", "content writer", "brand",
                  "growth", "social media", "iklan"],
    "finance": ["finance", "accounting", "akuntansi", "financial", "keuangan", "tax",
                "audit", "pajak"],
    "business": ["business", "sales", "account manager", "business development", "bizdev",
                 "operations", "operasional", "product manager", "project manager"],
    "engineering": ["engineer", "mechanical", "electrical", "civil", "industrial",
                    "teknik", "iot", "embedded", "hardware"],
}

# Kata kunci jenjang pendidikan (di dalam deskripsi/requirement lowongan).
_EDU_KEYWORDS: dict[str, list[str]] = {
    "high_school": ["sma", "smk", "high school", "slta", "sederajat"],
    "diploma": ["diploma", "d3", "d4", "associate degree", "diploma iii"],
    "bachelor": ["s1", "bachelor", "sarjana", "strata 1", "s.kom", "s.t", "s.si",
                 "bachelor's", "bachelor’s"],
    "master": ["s2", "master", "magister", "strata 2", "master's", "master’s"],
    "doctorate": ["s3", "phd", "doctor", "doktor", "strata 3", "doctoral"],
}

# Peta tipe kerja (string sumber → kanonik).
_JOB_TYPE_MAP: dict[str, str] = {
    "full time": "full_time", "full-time": "full_time", "fulltime": "full_time",
    "permanent": "full_time", "tetap": "full_time", "full_time": "full_time",
    "part time": "part_time", "part-time": "part_time", "parttime": "part_time",
    "paruh waktu": "part_time", "part_time": "part_time",
    "contract": "contract", "kontrak": "contract",
    "internship": "internship", "magang": "internship", "intern": "internship",
    "freelance": "freelance", "freelancer": "freelance", "lepas": "freelance",
    "temporary": "temporary", "temp": "temporary", "sementara": "temporary",
}

_REMOTE_WORDS = ["remote", "work from home", "wfh", "jarak jauh", "dari rumah"]
_HYBRID_WORDS = ["hybrid", "hibrida", "on-site & remote", "mixed"]
_ABROAD_WORDS = ["abroad", "overseas", "international", "relocation", "visa sponsorship",
                 "luar negeri", "relokasi", "visa"]
_FRESHGRAD_WORDS = ["fresh grad", "fresh graduate", "freshgrad", "lulusan baru",
                    "entry level", "entry-level", "tanpa pengalaman", "no experience",
                    "baru lulus"]

# Alias tipe kerja kanonik → varian teks untuk deteksi fallback.
_JOB_TYPE_ALIASES: dict[str, list[str]] = {
    "full_time": ["full time", "full-time", "fulltime", "permanent", "tetap"],
    "part_time": ["part time", "part-time", "parttime", "paruh waktu"],
    "contract": ["contract", "kontrak"],
    "internship": ["intern", "internship", "magang"],
    "freelance": ["freelance", "freelancer", "lepas"],
    "temporary": ["temporary", "temp", "sementara"],
}


@dataclass
class Filters:
    """State filter ter-normalisasi. Semua field opsional/default kosong."""

    locations: list[str] = field(default_factory=list)
    position_levels: list[str] = field(default_factory=list)
    job_types: list[str] = field(default_factory=list)
    specializations: list[str] = field(default_factory=list)
    education_levels: list[str] = field(default_factory=list)
    preferred_companies: list[str] = field(default_factory=list)
    excluded_companies: list[str] = field(default_factory=list)
    min_salary: float | None = None
    max_salary: float | None = None
    salary_currency: str = ""
    salary_not_specified: bool = False
    remote: bool = False
    hybrid: bool = False
    work_abroad: bool = False
    fresh_graduate: bool = False
    quick_response: bool = False
    sort_by: str = "relevance"

    def is_empty(self) -> bool:
        """True bila tidak ada filter aktif sama sekali."""
        return not (
            self.locations or self.position_levels or self.job_types
            or self.specializations or self.education_levels
            or self.preferred_companies or self.excluded_companies
            or self.min_salary or self.max_salary or self.remote
            or self.hybrid or self.work_abroad or self.fresh_graduate
            or self.quick_response
        )


def from_dict(data: dict[str, Any] | None) -> Filters:
    """Bangun Filters dari payload JSON frontend (toleran terhadap field hilang)."""
    if not data:
        return Filters()

    def lst(k: str) -> list[str]:
        v = data.get(k) or []
        return [str(x).strip() for x in v if str(x).strip()]

    def num(k: str) -> float | None:
        v = data.get(k)
        if v in (None, "", 0):
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    def flag(k: str) -> bool:
        return bool(data.get(k))

    return Filters(
        locations=lst("locations"),
        position_levels=[x for x in lst("position_levels") if x in POSITION_LEVELS],
        job_types=[x for x in lst("job_types") if x in JOB_TYPES],
        specializations=lst("specializations"),
        education_levels=[x for x in lst("education_levels") if x in EDUCATION_LEVELS],
        preferred_companies=lst("preferred_companies"),
        excluded_companies=lst("excluded_companies"),
        min_salary=num("min_salary"),
        max_salary=num("max_salary"),
        salary_currency=str(data.get("salary_currency") or "").upper(),
        salary_not_specified=flag("salary_not_specified"),
        remote=flag("remote"),
        hybrid=flag("hybrid"),
        work_abroad=flag("work_abroad"),
        fresh_graduate=flag("fresh_graduate"),
        quick_response=flag("quick_response"),
        sort_by=str(data.get("sort_by") or "relevance") if str(data.get("sort_by") or "relevance") in SORT_OPTIONS else "relevance",
    )


def to_dict(f: Filters) -> dict[str, Any]:
    """Serialize Filters → dict (untuk disimpan/response)."""
    return {
        "locations": f.locations,
        "position_levels": f.position_levels,
        "job_types": f.job_types,
        "specializations": f.specializations,
        "education_levels": f.education_levels,
        "preferred_companies": f.preferred_companies,
        "excluded_companies": f.excluded_companies,
        "min_salary": f.min_salary,
        "max_salary": f.max_salary,
        "salary_currency": f.salary_currency,
        "salary_not_specified": f.salary_not_specified,
        "remote": f.remote,
        "hybrid": f.hybrid,
        "work_abroad": f.work_abroad,
        "fresh_graduate": f.fresh_graduate,
        "quick_response": f.quick_response,
        "sort_by": f.sort_by,
    }


# ---------------------------------------------------------------------------
# Helper deteksi dari teks lowongan
# ---------------------------------------------------------------------------

def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip().lower()


def _norm_job_type(raw: str) -> str:
    """Map string job_type sumber → kanonik. Kosong bila tidak dikenali."""
    t = _normalize(raw)
    if not t:
        return ""
    return _JOB_TYPE_MAP.get(t, "")


def _job_full_text(job) -> str:
    return _normalize(
        " ".join(
            p for p in (job.title, job.company, job.description, job.requirements, job.job_type,
                        job.work_arrangement) if p
        )
    )


def _arrangement(job) -> str:
    """Kembalikan 'remote'|'hybrid'|'' berdasarkan field + teks."""
    txt = _normalize(" ".join(p for p in (job.work_arrangement, job.title, job.location) if p))
    if any(w in txt for w in _REMOTE_WORDS):
        return "remote"
    if any(w in txt for w in _HYBRID_WORDS):
        return "hybrid"
    return ""


def _highest_education_mentioned(text: str) -> str | None:
    """Jenjang pendidikan tertinggi yang disebut di teks lowongan (untuk syarat)."""
    best = None
    for level, kws in _EDU_KEYWORDS.items():
        if level == "doctorate" or level == "any":
            continue
        if any(k in text for k in kws):
            if best is None or _EDU_RANK[level] > _EDU_RANK[best]:
                best = level
    return best


# ---------------------------------------------------------------------------
# HARD FILTER — lowongan yang gagal dibuang
# ---------------------------------------------------------------------------

def _hard_location(job, f: Filters) -> bool:
    if not f.locations or "anywhere" in [x.lower() for x in f.locations] or "remote" in [x.lower() for x in f.locations]:
        return True
    loc = _normalize(job.location)
    if not loc:
        return True  # data lokasi kosong → jangan buang (sumber tidak isi)
    return any(x.lower() in loc for x in f.locations)


def _hard_job_type(job, f: Filters) -> bool:
    if not f.job_types:
        return True
    jt = _norm_job_type(job.job_type)
    if jt:
        return jt in f.job_types
    # Field kosong/tak dikenal → deteksi dari teks + judul.
    txt = _job_full_text(job)
    title = _normalize(job.title)
    for cand in f.job_types:
        for k in _JOB_TYPE_ALIASES.get(cand, []):
            if k in txt or k in title:
                return True
    return False


def _hard_salary(job, f: Filters) -> bool:
    if f.min_salary is None and f.max_salary is None:
        return True
    # Gaji lowongan kosong.
    jmin = job.salary_min
    jmax = job.salary_max
    if jmin is None and jmax is None:
        return f.salary_not_specified
    # Bila mata uang dipilih dan beda → bandingkan dengan konversi kasar (lihat _convert).
    if f.salary_currency and (job.currency or "").upper() != f.salary_currency:
        # konversi job ke mata uang preferensi
        jmin = _convert(jmin, (job.currency or "IDR").upper(), f.salary_currency)
        jmax = _convert(jmax, (job.currency or "IDR").upper(), f.salary_currency)

    eff_min = jmin if jmin is not None else jmax
    eff_max = jmax if jmax is not None else jmin
    if f.min_salary is not None and (eff_max is None or eff_max < f.min_salary):
        return False
    if f.max_salary is not None and (eff_min is not None and eff_min > f.max_salary):
        return False
    return True


# Kurs kasar (per 1 unit ke IDR) — cukup untuk filter, bukan untuk konversi presisi.
_EXCHANGE_TO_IDR = {"IDR": 1.0, "USD": 15700.0, "SGD": 11800.0, "EUR": 17200.0}


def _convert(amount: float | None, frm: str, to: str) -> float | None:
    if amount is None:
        return None
    if not frm or not to or frm == to:
        return amount
    idr = amount * _EXCHANGE_TO_IDR.get(frm, 1.0)
    return idr / _EXCHANGE_TO_IDR.get(to, 1.0)


def _hard_education(job, f: Filters) -> bool:
    """Buang lowongan yang mempersyaratkan jenjang > jenjang tertinggi user."""
    if not f.education_levels or "any" in f.education_levels:
        return True
    required = _highest_education_mentioned(_job_full_text(job))
    if required is None:
        return True  # tidak ada syarat eksplisit → lolos
    user_max = max((_EDU_RANK[l] for l in f.education_levels if l in _EDU_RANK), default=2)
    return _EDU_RANK[required] <= user_max


def _hard_company(job, f: Filters) -> bool:
    if not f.excluded_companies:
        return True
    comp = _normalize(job.company)
    return not any(x.lower() in comp for x in f.excluded_companies)


def _hard_arrangement(job, f: Filters) -> bool:
    """Bila remote/hybrid dipilih EKSPLISIT, jadikan filter keras."""
    if not f.remote and not f.hybrid:
        return True
    arr = _arrangement(job)
    if f.remote and not f.hybrid:
        return arr == "remote"
    if f.hybrid and not f.remote:
        return arr == "hybrid"
    # keduanya dipilih → remote ATAU hybrid boleh
    return arr in ("remote", "hybrid")


def passes_hard_filters(job, f: Filters) -> bool:
    """Agregator hard filter. True = lolos (tetap di pool)."""
    return (
        _hard_location(job, f)
        and _hard_job_type(job, f)
        and _hard_salary(job, f)
        and _hard_education(job, f)
        and _hard_company(job, f)
        and _hard_arrangement(job, f)
    )


# ---------------------------------------------------------------------------
# SOFT PREFERENCE — boost skor + alasan
# ---------------------------------------------------------------------------

def preference_boost(job, f: Filters) -> tuple[float, list[str]]:
    """Hitung boost 0..1 + daftar alasan ("kenapa cocok").

    Soft preferences TIDAK membuang lowongan; hanya menaikkan skor & menjelaskan.
    """
    boost = 0.0
    reasons: list[str] = []

    if f.is_empty():
        return 0.0, []

    txt = _job_full_text(job)
    title = _normalize(job.title)
    # Teks "kategori" (judul + skill + tipe kerja) untuk sinyal spesialisasi/level
    # yang lebih presisi — deskripsi terlalu berisik untuk kategori.
    cat_txt = _normalize(
        " ".join(p for p in (job.title, " ".join(job.skills or []), job.job_type) if p)
    )

    # Lokasi eksplisit (yang lolos hard filter pasti match → beri alasan).
    if f.locations and not any(x.lower() in ("anywhere", "remote") for x in f.locations):
        if any(x.lower() in _normalize(job.location) for x in f.locations):
            reasons.append("Lokasi sesuai preferensi")
            boost += 0.03

    # Level posisi.
    if f.position_levels:
        for lv in f.position_levels:
            if any(k in title or k in cat_txt for k in _POSITION_KEYWORDS.get(lv, [])):
                reasons.append(f"Level posisi: {_label(lv)}")
                boost += 0.04
                break

    # Spesialisasi (boost terkuat — inti pencarian). Cocok ke judul+skill+tipe.
    if f.specializations:
        for spec in f.specializations:
            if any(k in cat_txt for k in _SPEC_KEYWORDS.get(spec, [])):
                reasons.append(f"Bidang: {_label(spec)}")
                boost += 0.06
                break

    # Perusahaan pilihan.
    if f.preferred_companies:
        comp = _normalize(job.company)
        if any(x.lower() in comp for x in f.preferred_companies):
            reasons.append("Perusahaan pilihan")
            boost += 0.10

    # Gaji di atas minimum (soft — yang di bawah min sudah dibuang hard).
    if f.min_salary is not None:
        jmin = job.salary_min
        jmax = job.salary_max
        cur = (job.currency or "IDR").upper()
        if f.salary_currency and cur != f.salary_currency:
            jmin = _convert(jmin, cur, f.salary_currency)
            jmax = _convert(jmax, cur, f.salary_currency)
        if jmax is not None and jmax >= f.min_salary:
            reasons.append("Gaji memenuhi minimum")
            boost += 0.04

    # Remote / hybrid.
    arr = _arrangement(job)
    if f.remote and arr == "remote":
        reasons.append("Remote (WFH)")
        boost += 0.03
    if f.hybrid and arr == "hybrid":
        reasons.append("Hybrid")
        boost += 0.03

    # Bekerja di luar negeri.
    if f.work_abroad and any(w in txt for w in _ABROAD_WORDS):
        reasons.append("Peluang internasional")
        boost += 0.05

    # Fresh graduate.
    if f.fresh_graduate and any(w in txt for w in _FRESHGRAD_WORDS):
        reasons.append("Menerima fresh graduate")
        boost += 0.05

    # Quick response (proxy: lowongan baru = rekruter aktif).
    if f.quick_response and _is_recent(job.posted_at):
        reasons.append("Baru diposting (respons cepat)")
        boost += 0.03

    return min(0.35, boost), reasons


def _is_recent(posted_at: str, days: int = 7) -> bool:
    """Cek apakah lowongan diposting < N hari lalu (best-effort parse)."""
    if not posted_at:
        return False
    s = _normalize(posted_at)
    try:
        # ISO timestamp (banyak sumber).
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - dt).days < days
    except ValueError:
        pass
    # Teks relatif: "3 hari yang lalu", "2 days ago".
    m = re.search(r"(\d+)\s*(hari|day|jam|hour|minggu|week)", s)
    if m:
        n = int(m.group(1))
        unit = m.group(2)
        if unit in ("jam", "hour"):
            return n < days * 24
        if unit in ("hari", "day"):
            return n < days
        if unit in ("minggu", "week"):
            return n * 7 < days
    return False


def _label(key: str) -> str:
    """Label tampil singkat untuk alasan (id → judul)."""
    return {
        "internship": "Internship", "fresh_graduate": "Fresh Graduate",
        "entry": "Entry", "junior": "Junior", "mid": "Mid", "senior": "Senior",
        "manager": "Manager",
        "software_engineering": "Software Engineering",
        "network_engineering": "Network Engineering", "it_support": "IT Support",
        "data_science": "Data Science", "cybersecurity": "Cybersecurity",
        "ui_ux": "UI/UX", "marketing": "Marketing", "finance": "Finance",
        "business": "Business", "engineering": "Engineering",
    }.get(key, key.replace("_", " ").title())


def sort_results(results: list[dict], sort_by: str) -> list[dict]:
    """Urutkan hasil match sesuai preferensi sort."""
    if sort_by == "latest":
        return sorted(results, key=lambda r: _posted_ts(r.get("posted_at")), reverse=True)
    if sort_by == "salary_desc":
        return sorted(results, key=lambda r: r.get("salary_max") or r.get("salary_min") or 0, reverse=True)
    if sort_by == "salary_asc":
        return sorted(results, key=lambda r: r.get("salary_max") or r.get("salary_min") or float("inf"))
    if sort_by == "match_score":
        return sorted(results, key=lambda r: r.get("score", 0), reverse=True)
    return sorted(results, key=lambda r: r.get("score", 0), reverse=True)  # relevance


def _posted_ts(posted_at: str) -> float:
    """Timestamp kasar untuk sort latest (0 bila tak bisa parse)."""
    if not posted_at:
        return 0.0
    try:
        dt = datetime.fromisoformat(_normalize(posted_at).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except ValueError:
        return 0.0
