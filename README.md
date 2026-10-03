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
.venv/Scripts/python -m scripts.warmup_model              # unduh model embedding (sekali)
.venv/Scripts/python -m uvicorn app.main:app --reload
```

Buka http://localhost:8000/docs untuk API docs.

## API endpoints

| Method | Path | Fungsi |
|---|---|---|
| GET | `/health` | Cek status |
| POST | `/api/cv/upload` | Upload CV (PDF/DOCX) → ekstrak teks |
| POST | `/api/jobs/refresh` | Fetch + embed + simpan lowongan (dedupe) |
| GET | `/api/jobs` | Baca lowongan tersimpan (filter `source`, `limit`) |
| POST | `/api/match` | Upload CV → matching (fetch+embed+score+urutkan) |

## Verifikasi

```bash
cd backend
.venv/Scripts/python -m scripts.verify_fetchers   # cek fetcher (data live)
.venv/Scripts/python -m scripts.verify_matching   # cek matching end-to-end
```

## Rencana lengkap & deployment

Lihat `PLAN.md` (rencana) dan `DEPLOYMENT.md` (kendala hosting free-tier).
