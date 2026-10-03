# JobMatch

Job seeker automation: upload CV (PDF/DOCX) → otomatis pantau lowongan dari
beberapa portal (JobStreet, Glints, ...) → tampilkan yang cocok secara semantik
dengan skor + alasan kecocokan.

## Arsitektur

```
frontend/  (Next.js · React · TypeScript)  ──▶  Vercel (gratis)
backend/   (FastAPI · Python)              ──▶  Render/Railway (gratis)
              ├─ fetchers/  (JobStreet v5, Glints searchJobsV3, ...)
              ├─ matching/  (sentence-transformers embedding + cosine)
              ├─ scheduler/ (APScheduler, fetch berkala + dedupe)
              └─ DB         (SQLite dev → Postgres+pgvector produksi)
```

## Sumber lowongan (status)

| Sumber | Endpoint | Status |
|---|---|---|
| JobStreet | `GET id.jobstreet.com/api/jobsearch/v5/search` | ✅ terverifikasi |
| Glints | `POST glints.com/api/v2-alc/graphql` (searchJobsV3) | ✅ terverifikasi |
| LinkedIn | guest API | ⚠️ opsional (ToS + anti-bot) |

## Jalankan backend (development)

```bash
cd backend
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # Windows
.venv/Scripts/python -m uvicorn app.main:app --reload
```

Buka http://localhost:8000/docs untuk API docs.

## Verifikasi fetcher

```bash
cd backend
.venv/Scripts/python -m scripts.verify_fetchers
```

## Rencana lengkap

Lihat `PLAN.md`.
