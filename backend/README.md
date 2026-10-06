---
title: JobMatch Backend
emoji: 💼
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
---

# JobMatch Backend API

Backend untuk **JobMatch** — job seeker automation (CV matching terhadap ribuan
lowongan dari 6 portal Indonesia).

- **Frontend** (Next.js): https://github.com/Anggito007/jobmatch (folder `frontend/`)
- **API docs**: buka `<spaces-url>/docs`

## Endpoints

| Method | Path | Fungsi |
|---|---|---|
| GET | `/health` | Cek status |
| POST | `/api/match` | Upload CV → matching semantik |
| POST | `/api/jobs/refresh` | Fetch + embed + simpan pool lowongan |
| POST | `/api/auth/register` | Daftar akun |
| POST | `/api/auth/login` | Masuk → token |
| POST | `/api/feedback` | 👍/👎 relevansi |
| GET/POST/DELETE | `/api/saved` | Simpan lowongan + status lamaran |
| POST | `/api/digest` | Email digest (Gmail SMTP) |

## Environment variables (opsional)

- `DATABASE_URL` — default SQLite di `/data/jobmatch.db` (persistent)
- `CORS_ORIGINS` — default `*` (izinkan semua origin; auth pakai Bearer token, bukan cookie)
- `FETCH_INTERVAL_HOURS` — interval scheduler (default 6)
- `SMTP_USER` / `SMTP_PASSWORD` — untuk kirim email digest (App Password Gmail)

> Catatan: Spaces free tier punya *cold start* — saat pertama diakses setelah idle,
> proses bangun ~1-2 menit.
