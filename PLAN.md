# Job Seeker Automation — Rencana Implementasi

> **Goal:** Web app multi-pengguna yang menerima upload CV (PDF/DOCX), otomatis memantau lowongan kerja dari beberapa portal (JobStreet, Glints, LinkedIn, dll.), dan menampilkan lowongan yang cocok secara semantik dengan skor + alasan kecocokan.

**Architecture:** Backend Python (FastAPI) dengan pola *adapter* per sumber lowongan (semua hasil dinormalisasi ke satu schema `Job`), CV di-embed dan dibandingkan cosine similarity terhadap embedding lowongan, job di-fetch berkala oleh scheduler dan di-dedupe. Frontend dashboard menampilkan lowongan terurut skor.

**Tech Stack:** Python 3.11+, FastAPI + Uvicorn, SQLite (MVP) → PostgreSQL + pgvector (produksi), sentence-transformers (embedding multibahasa), httpx (fetch), APScheduler (jadwal), Jinja2 + HTMX (frontend MVP) → React (opsional polish).

---

## Keputusan yang sudah diambil

| Aspek | Keputusan |
|---|---|
| Bentuk | Web app + dashboard |
| Stack | Python (rekomendasi) |
| Tujuan | Pribadi + portofolio, bisa diakses publik |
| Matching | Semantic (embedding), bukan keyword saja |

---

## 1. Arsitektur

```
┌─────────────┐   upload CV (PDF/DOCX)    ┌──────────────┐
│   Browser   │ ─────────────────────────▶│   FastAPI    │
│ (Dashboard) │ ◀─── JSON lowongan+skor ──│   Backend    │
└─────────────┘                            └──────┬───────┘
                                                  │
              ┌──────────────────┬────────────────┼─────────────┐
              ▼                  ▼                ▼             ▼
        ┌──────────┐      ┌──────────┐     ┌──────────┐  ┌───────────┐
        │ JobStreet│      │  Glints  │     │ LinkedIn │  │ Dealls/…  │
        │ (JSON API)│      │(GraphQL) │     │(guest API)│  │(HTML)     │
        └──────────┘      └──────────┘     └──────────┘  └───────────┘
              └──────────────────┬────────────────┘
                                 ▼
                        ┌─────────────────┐
                        │  Normalizer →   │
                        │  Unified `Job`  │──▶ SQLite/Postgres
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │ Embedder +      │
                        │ cosine sim      │──▶ skor + alasan cocok
                        └─────────────────┘
```

### Komponen

1. **CV Ingestion** — upload PDF/DOCX → ekstrak teks (`pdfplumber`, `python-docx`) → ekstrak profil terstruktur (skills, jabatan, pengalaman, pendidikan) → embed.
2. **Job Fetchers (adapters)** — satu kelas per sumber, interface seragam `fetch(keywords) -> list[Job]`.
3. **Scheduler** — `APScheduler`, fetch berkala (per jam/hari), dedupe by `source + external_id`.
4. **Matching Engine** — embed judul+deskripsi lowongan, cosine similarity vs embedding CV, ditambah skor overlap skill eksplisit.
5. **Dashboard** — daftar lowongan terurut skor, filter (lokasi/jenis/sumber), simpan, link apply.
6. **Notifikasi** (opsional) — email digest harian.

---

## 2. Sumber Lowongan (prioritas berdasarkan kemudahan & legalitas)

| Sumber | Cara akses | Auth | Risiko |
|---|---|---|---|
| **JobStreet** (`id.jobstreet.com`) | Public JSON API `GET /api/chalice-search/v4/search?siteKey=ID-Main&keywords=…&location=…` (grup SEEK) | Tanpa key | Rendah — start dari sini |
| **Glints** (`glints.com/id`) | Public GraphQL `POST /api/graphql` (schema reverse-engineered) | Tanpa auth | Rendah–sedang |
| **LinkedIn** | Guest jobs API `jobs-guest/jobs/api/seeMoreJobPostings/search` | Tanpa login | **Tinggi** — ToS + anti-bot, jadikan opsional |
| Dealls, Karir.com | HTML scraping (Playwright/httpx) | — | Sedang — fase lanjut |
| Kalibrr, KitaLulus | API internal terkunci / app-only | — | Skip dulu (perlu Playwright/proxy) |

Referensi implementasi nyata: repo `ceroberoz/id-jobs` dan `santifer/career-ops` (dokumentasi endpoint publik yang sama).

**Unified `Job` schema:**

```python
{
  "id": "jobstreet:ab12cd",       # source + external_id
  "source": "jobstreet",
  "title": "Backend Engineer",
  "company": "PT Contoh",
  "location": "Bandung",
  "salary_min": 5000000, "salary_max": 8000000, "currency": "IDR",
  "job_type": "Full-time", "work_arrangement": "Hybrid",
  "description": "...", "requirements": "...",
  "skills": ["Python", "FastAPI", "PostgreSQL"],
  "url": "https://...",           # link apply
  "posted_at": "2026-09-28T00:00:00Z",
  "fetched_at": "2026-09-30T09:00:00Z"
}
```

---

## 3. Matching Engine

1. CV dipadatkan jadi satu teks: `skills + jabatan target + ringkasan`.
2. Embed pakai **sentence-transformers** model multibahasa `paraphrase-multilingual-MiniLM-L12-v2` (mendukung Bahasa Indonesia + Inggris, gratis, jalan lokal — tanpa biaya API).
3. Tiap lowongan di-embed dari `title + description + requirements`.
4. **Skor = cosine similarity(cv_vec, job_vec)** dinormalisasi 0–1, dikombinasi dengan **skill-overlap score** (skill CV ∩ skill lowongan) sebagai sinyal kedua.
5. Dashboard menampilkan **"kenapa cocok"**: daftar skill yang match + kalimat dari deskripsi yang paling relevan.

Catatan biaya: embedding lokal = gratis. Upgrade ke OpenAI/embedding API lain opsional, tinggal ganti backend embedder.

---

## 4. Struktur Proyek

```
jobseeker-automation/
├── app/
│   ├── main.py               # FastAPI app + routes
│   ├── config.py             # env, settings
│   ├── models.py             # SQLAlchemy models (User, Job, Match)
│   ├── schemas.py            # Pydantic
│   ├── db.py                 # session
│   ├── cv/
│   │   ├── extract.py        # PDF/DOCX → teks
│   │   └── profile.py        # ekstrak skills/jabatan/pengalaman
│   ├── fetchers/
│   │   ├── base.py           # interface adapter
│   │   ├── jobstreet.py
│   │   ├── glints.py
│   │   └── linkedin.py       # opsional
│   ├── matching/
│   │   ├── embedder.py       # sentence-transformers wrapper
│   │   └── scorer.py         # cosine + skill overlap
│   ├── scheduler.py          # APScheduler jobs
│   └── templates/            # Jinja2 dashboard
├── tests/
├── requirements.txt
└── Dockerfile
```

---

## 5. Roadmap (fase)

### Fase 0 — Setup (rangkai kerangka)
Buat venv, `requirements.txt`, FastAPI "hello", struktur folder, git init. **Kriteria:** `uvicorn app.main:app` jalan, `/health` 200.

### Fase 1 — MVP (1 sumber + 1 user)
- CV upload PDF/DOCX → ekstrak teks + skills.
- Fetcher **JobStreet** (JSON API) → simpan ke SQLite.
- Embedding + cosine matching → skor.
- Dashboard sederhana (Jinja2 + HTMX): upload CV, lihat lowongan terurut skor.
- Scheduler fetch harian + dedupe.
**Kriteria:** upload CV nyata → muncul daftar lowongan JobStreet dengan skor relevan.

### Fase 2 — Tambah sumber
- Fetcher **Glints** (GraphQL) + normalisasi.
- **LinkedIn** (opsional, rate rendah, toggled off by default).
- Pindah SQLite → PostgreSQL + pgvector, FAISS opsional.
- "Kenapa cocok" (highlight skill + kalimat relevan).

### Fase 3 — Multi-pengguna + notifikasi + deploy
- Auth (register/login JWT), CV per user, preferensi (kata kunci, lokasi).
- Email digest harian (opsional).
- Docker + deploy ke Render/Railway/Fly.io (free tier) atau VPS.
- (Opsional) React frontend untuk polish portofolio.

---

## 6. Risiko & mitigasi

| Risiko | Mitigasi |
|---|---|
| LinkedIn ToS/anti-bot → akun/ip diblokir | Jadikan opsional, rate rendah, prioritaskan JobStreet+Glints |
| Endpoint API (undocumented) berubah tiba-tiba | Pola adapter → kerusakan terisolasi per sumber |
| Biaya embedding/LLM | sentence-transformers lokal (gratis); API eksternal opsional |
| Biaya hosting (target publik) | Free tier (Render/Railway/Fly), Postgres free (Neon/Supabase) |
| Duplikasi lowongan antar fetch | Dedupe by `source+external_id`, upsert |

---

## 7. Keputusan final

| # | Topik | Keputusan |
|---|---|---|
| 1 | Nama produk | **JobMatch** |
| 2 | Notifikasi | Dashboard dulu; email (Gmail) menyusul setelah core stabil |
| 3 | Frontend | **Next.js (React) + TypeScript** — standar proper, mulus di Vercel |
| 4 | Hosting | **Frontend → Vercel (gratis)** · **Backend → Render/Railway free tier** · **DB → Neon/Supabase Postgres (gratis)** |

> Catatan arsitektur penting: Vercel hanya untuk frontend. Backend (scheduler + embedding + scraping) TIDAK bisa di Vercel karena butuh proses berjalan terus, model AI ~100MB+, dan scraping durasi panjang — harus di Render/Railway (free tier). Dua deployment + satu Postgres, semua gratis.

**Struktur repo final:**

```
jobseeker-automation/
├── backend/            # FastAPI (Python) — API, scraper, matching, scheduler
└── frontend/           # Next.js (React/TS) — dashboard, deploy Vercel
```
