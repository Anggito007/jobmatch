# JobMatch

Job seeker automation: upload CV (PDF/DOCX) → pindai ribuan lowongan dari
**6 portal** → tampilkan yang cocok secara semantik dengan skor + alasan
kecocokan (CV adalah filter utama, bukan kata kunci).

## Arsitektur

```
frontend/  (Next.js · React · TypeScript)  ──▶  Vercel (gratis)
backend/   (FastAPI · Python)              ──▶  Render/Railway/VPS
              ├─ fetchers/  (6 sumber: JobStreet, Glints, Dealls, Kalibrr,
              │              Karir, TechInAsia)
              ├─ matching/  (embedding + cosine + skill + lexical hybrid)
              ├─ scheduler/ (APScheduler, fetch berkala + dedupe)
              └─ DB         (SQLite dev → Postgres+pgvector produksi)
```

## Sumber lowongan (status)

| Sumber | Endpoint | Status |
|---|---|---|
| JobStreet | `GET id.jobstreet.com/api/jobsearch/v5/search` | ✅ terverifikasi |
| Glints | `POST glints.com/api/v2-alc/graphql` (searchJobsV3) | ✅ terverifikasi |
| Dealls | `GET api.sejutacita.id/v1/explore-job/job` | ✅ terverifikasi |
| Kalibrr | `GET kalibrr.com/kjs/job_board/search` (feed penuh ~1200) | ✅ terverifikasi |
| Karir.com | `POST gateway2-beta.karir.com/v2/search/opportunities` | ✅ terverifikasi |
| TechInAsia Jobs | Algolia `219WX3MPV4` index `job_postings` | ✅ terverifikasi |
| LinkedIn | guest API | ⚠️ opsional (ToS + anti-bot) |

## Cara kerja matching

1. Scheduler mengumpulkan pool lowongan (broad, ribuan) dari 6 sumber → embed → simpan.
2. Upload CV → ekstrak skill + embed.
3. Skor hybrid tiap lowongan: `0.45·cosine + 0.30·skill_overlap + 0.25·lexical_overlap`.
4. Urutkan + diversifikasi (batasi dominasi satu perusahaan/sumber).

## Menjalankan & menghentikan (Windows — cara termudah)

Dua file batch di root project:

| File | Fungsi |
|---|---|
| **`start.bat`** | Menyalakan backend (port 8000) + frontend (port 3000) di dua jendela terpisah, menunggu server siap, lalu memverifikasi keduanya dan menampilkan URL. |
| **`stop.bat`** | Menghentikan kedua server (tutup jendela + sapu proses yang masih memegang port 8000/3000), lalu memverifikasi port sudah kosong. |

Cukup **klik dua kali** `start.bat` untuk mulai, `stop.bat` untuk berhenti.

`start.bat` juga otomatis menjalankan `npm install` bila `frontend/node_modules` belum ada, dan memperingatkan bila virtualenv backend belum dibuat.

## Jalankan manual (development)

```bash
cd backend
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # Windows
.venv/Scripts/python -m scripts.warmup_model              # unduh model embedding (sekali)
.venv/Scripts/python -m uvicorn app.main:app --reload
```

Buka http://localhost:8000/docs untuk API docs.

## API endpoints

| Method | Path | Fungsi | Auth |
|---|---|---|---|
| GET | `/health` | Cek status | — |
| POST | `/api/cv/upload` | Upload CV (PDF/DOCX) → ekstrak teks | — |
| POST | `/api/jobs/refresh` | Fetch + embed + simpan pool lowongan (dedupe) | — |
| GET | `/api/jobs` | Baca lowongan tersimpan (filter `source`, `limit`) | — |
| POST | `/api/match` | Upload CV → matching terhadap pool (skor + urutkan) | opsional |
| POST | `/api/auth/register` | Daftar akun | — |
| POST | `/api/auth/login` | Masuk → token | — |
| GET | `/api/auth/me` | Info akun aktif | ✅ |
| POST | `/api/feedback` | Tandai lowongan relevan/tidak (👍/👎) | ✅ |
| GET / POST / DELETE | `/api/saved` | Simpan / lihat / hapus lowongan + status lamaran | ✅ |
| POST | `/api/digest` | Kirim email digest lowongan cocok (Gmail SMTP) | ✅ |

Auth pakai header `Authorization: Bearer <token>`.

## Sampel CV untuk pengujian

Di `samples/` ada 3 CV sampel (`.txt` + `.docx`): `backend_engineer`,
`data_analyst`, `iot_engineer`. Regenerate kapan saja dengan:
`python samples/make_test_cvs.py`.

## Verifikasi

```bash
cd backend
.venv/Scripts/python -m scripts.verify_fetchers   # cek fetcher (data live)
.venv/Scripts/python -m scripts.verify_matching   # cek matching end-to-end
```

## Rencana lengkap & deployment

Lihat `PLAN.md` (rencana) dan `DEPLOYMENT.md` (kendala hosting free-tier).
