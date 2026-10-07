# JobMatch — Dokumentasi Proyek Lengkap

> **Status terkini:** MVP fungsional (Fase A–C selesai), akurasi matching sudah
> ditingkatkan dengan deskripsi lengkap + preferensi target posisi. **Hosting
> ditunda** (kendala kartu kredit). Fokus sekarang: pengembangan & pengujian lokal.

---

## 1. Ringkasan

**JobMatch** adalah aplikasi *job seeker automation*: pengguna mengunggah CV
(PDF/DOCX/TXT), sistem memindai ribuan lowongan kerja dari **6 portal Indonesia**,
lalu menampilkan lowongan yang paling cocok **secara semantik** (bukan sekadar
kata kunci), lengkap dengan skor kecocokan dan alasan (skill yang match).

Kebutuhan awal pengguna: *"tracking lowongan kerja yang sesuai dengan CV yang
di-upload, dari berbagai website seperti LinkedIn, Glints, dan sebagainya."*

---

## 2. Arsitektur

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (Next.js 15 · React 19 · TypeScript)              │
│  Dashboard: upload CV, preferensi, lihat hasil, simpan       │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP (REST + multipart)
┌──────────────────────────▼──────────────────────────────────┐
│  Backend (FastAPI · Python 3.14)                            │
│  ├─ fetchers/   6 sumber lowongan (adapter pattern)         │
│  ├─ cv/         ekstraksi teks + profil CV                  │
│  ├─ matching/   embedding + scoring (cosine/skill/lexical)  │
│  ├─ scheduler/  APScheduler fetch berkala + dedupe          │
│  └─ DB          SQLite (dev) → Postgres (produksi)          │
└─────────────────────────────────────────────────────────────┘
```

**Prinsip desain kunci:** *adapter pattern* — setiap sumber lowongan diisolasi
di kelas sendiri. Jika satu portal mengubah API-nya, hanya satu file yang
diperbaiki, sisanya tidak terganggu.

---

## 3. Sumber Lowongan (6 portal, semua tanpa API key)

| Sumber | Endpoint | Deskripsi lengkap? | Status |
|---|---|---|---|
| **JobStreet** | `GET id.jobstreet.com/api/jobsearch/v5/search` | teaser singkat | ✅ |
| **Glints** | `POST glints.com/api/v2-alc/graphql` (`searchJobsV3`) | via JSON-LD detail | ✅ |
| **Kalibrr** | `GET kalibrr.com/kjs/job_board/search` (feed ~1200) | langsung di search | ✅ |
| **Karir.com** | `POST gateway2-beta.karir.com/v2/search/opportunities` | via `_next/data` | ✅ |
| **Dealls** | `GET api.sejutacita.id/v1/explore-job/job` | skill + gaji | ✅ |
| **TechInAsia Jobs** | Algolia `219WX3MPV4` index `job_postings` | deskripsi penuh | ✅ |
| LinkedIn | guest API | — | ⚠️ **belum** (ToS ketat) |

Pool terakhir saat dibangun: **~1.700 lowongan**.

> Catatan penting: `santifer/career-ops` dan `ceroberoz/id-jobs` (GitHub) adalah
> referensi utama untuk endpoint publik yang masih hidup.

---

## 4. Alur Matching (cara sistem memutuskan "cocok")

### 4.1 Pipeline

1. **Upload CV** → ekstrak teks (pdfplumber / python-docx).
2. **Parsing profil** → skill (word-boundary match), tahun pengalaman, pendidikan,
   target role.
3. **Embedding** → CV diubah jadi vektor 384 dimensi.
4. **Skor semua lowongan** di pool terhadap CV.
5. **Urutkan + diversifikasi** → tampilkan top-N.

### 4.2 Skor hibrid

```
skor = 0.45·cosine  +  0.30·skill_overlap  +  0.25·lexical_overlap
```

- **Cosine** — kemiripan semantik (embedding multibahasa MiniLM).
- **Skill overlap** — Jaccard antara skill CV vs skill lowongan.
- **Lexical overlap** — berapa kata kunci CV muncul di lowongan (judul diberi
  bobot ganda).

### 4.3 Preferensi target posisi (fitur kunci terbaru)

Menjawab kebutuhan: *"bisa web tapi mau cari IoT"* — sistem tidak hanya menjawab
**"kamu bisa apa"** (dari CV), tapi juga **"kamu mau ke mana"**.

- Kolom `preference` di form → embedding preferensi di-**blend** dengan vektor CV
  (default 65% preferensi / 35% CV).
- **Boost leksikal tegas**: lowongan yang menyebut kata kunci preferensi
  (IoT/ESP32/LoRa/dll.) naik +0.08/hit (maks +0.30), sehingga langsung ke puncak.
- Skill preferensi ditambahkan ke set skill target.

**Hasil uji nyata:** CV murni web + preferensi "IoT embedded ESP32 LoRa" →
"Network & IoT Officer" melompat dari tidak ada → **posisi #1**.

### 4.4 Diversifikasi

Batasi dominasi (maks 2 per perusahaan, 8 per sumber) supaya top-N mewakili
banyak sumber, bukan didominasi satu agency (mis. SIGMATECH yang spam lowongan).

---

## 5. Embedding Model (ML, bukan LLM)

Sistem memakai **machine learning (embedding)**, bukan LLM generatif.

- **Model:** `paraphrase-multilingual-MiniLM-L12-v2` (384 dimensi, 50+ bahasa
  termasuk Indonesia).
- **Backend runtime ganda (auto-detect):**
  - `fastembed` (ONNX, ~200MB) — default, untuk hosting ringan (Render free).
  - `sentence-transformers` (torch, ~1GB) — fallback kualitas penuh (VPS/Oracle).
  - **Model-nya sama** → akurasi identik, hanya runtime yang beda.
- **Tidak ada LLM** — tidak ada generasi teks, tidak ada biaya API bulanan.

> Catatan teknis penting: `fastembed` TIDAK menormalisasi vektor output; kode
> kami menormalisasi manual di `embedder.py` supaya cosine valid.

---

## 6. Fitur yang Sudah Ada

| Fitur | Status |
|---|---|
| Upload CV (PDF/DOCX/TXT) + drag-drop | ✅ |
| Parsing CV (skill, tahun, pendidikan, target role) | ✅ |
| Matching semantik 6 sumber | ✅ |
| Preferensi target posisi (steering) | ✅ |
| Scheduler fetch berkala (APScheduler) | ✅ |
| Dedupe lowongan (`source+external_id`) | ✅ |
| Auth multi-user (register/login, pbkdf2, token) | ✅ |
| Simpan lowongan + status lamaran | ✅ |
| Email digest harian (SMTP, butuh kredensial) | ✅ kode jadi |
| Dashboard dark-mode responsif | ✅ |

**Dihapus (keputusan user):** fitur feedback 👍/👎 — user akan mengumpulkan
label data secara manual.

---

## 7. Struktur Proyek

```
jobseeker-automation/
├── backend/                    # FastAPI (Python)
│   ├── app/
│   │   ├── main.py             # entrypoint + router + CORS
│   │   ├── config.py           # settings (env)
│   │   ├── db.py               # SQLAlchemy engine
│   │   ├── models.py           # Job, User, AuthSession, SavedJob, CVProfile
│   │   ├── auth.py             # hash password + token sesi
│   │   ├── email.py            # SMTP digest
│   │   ├── store.py            # upsert/dedupe + save/list
│   │   ├── scheduler.py        # APScheduler + collect_jobs
│   │   ├── cv/                 # extract.py (PDF/DOCX), profile.py (parsing)
│   │   ├── fetchers/           # base + 6 adapter + utils
│   │   ├── matching/           # embedder, scorer, skills
│   │   └── routers/            # auth, cv, jobs, match, saved, email
│   ├── scripts/                # warmup_model, verify_fetchers, verify_matching
│   ├── requirements.txt        # fastembed (ringan)
│   ├── requirements-torch.txt  # torch penuh (opsional)
│   ├── Dockerfile              # untuk Render/VPS
│   └── render.yaml             # (dipindah ke root, lihat catatan)
├── frontend/                   # Next.js (React/TS)
│   ├── app/                    # layout, page (dashboard), globals.css
│   ├── components/             # CvUpload, JobCard, AuthForm
│   └── lib/api.ts              # klien API + tipe
├── samples/                    # 3 CV sampel (.docx/.txt) + generator
├── scripts/                    # deploy Oracle + HTTPS
├── .github/workflows/          # cron eksternal (refresh tiap 6 jam)
├── render.yaml                 # blueprint Render (di ROOT)
├── DEPLOYMENT.md               # panduan hosting
├── PLAN.md                     # rencana pengembangan
└── README.md                   # ringkasan + endpoint
```

---

## 8. API Endpoints

Base URL lokal: `http://localhost:8000`

| Method | Path | Fungsi | Auth |
|---|---|---|---|
| GET | `/health` | cek status | — |
| POST | `/api/cv/upload` | upload CV → ekstrak teks | — |
| POST | `/api/jobs/refresh` | fetch + embed + simpan pool | — |
| GET | `/api/jobs` | baca lowongan tersimpan | — |
| POST | `/api/match` | upload CV → matching (skor + urutkan) | opsional |
| POST | `/api/auth/register` | daftar akun | — |
| POST | `/api/auth/login` | masuk → token | — |
| GET | `/api/auth/me` | info akun | ✅ |
| GET/POST/DELETE | `/api/saved` | simpan/lihat/hapus lowongan | ✅ |
| POST | `/api/digest` | kirim email digest | ✅ |

Auth: header `Authorization: Bearer <token>`.

---

## 9. Cara Menjalankan (Lokal / Development)

### Prasyarat
- Python 3.14 (dipakai), atau 3.12
- Node.js ≥ 18

### Backend
```bash
cd backend
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # Windows
.venv/Scripts/python -m scripts.warmup_model              # unduh model (sekali)
.venv/Scripts/python -m uvicorn app.main:app --reload
```

### Frontend (terminal terpisah)
```bash
cd frontend
npm install
npm run dev
```

Buka `http://localhost:3000` (dashboard) dan `http://localhost:8000/docs` (API).

> Catatan Windows: `uvicorn` dipasang **tanpa `[standard]`**, jadi `--reload`
> tidak jalan (butuh watchfiles yang tidak punya wheel cp314). Restart manual.

---

## 10. Pengujian

- **CV sampel** di `samples/` (backend / data analyst / IoT), format `.docx` + `.txt`.
  Regenerate: `python samples/make_test_cvs.py`.
- **Verifikasi fetcher**: `python -m scripts.verify_fetchers`
- **Verifikasi matching end-to-end**: `python -m scripts.verify_matching`

---

## 11. Status Hosting (DITUNDA)

**Kendala:** backend (~200MB dengan fastembed) butuh server yang selalu nyala,
tapi semua hosting gratis "selalu nyala" (Oracle, Render, Koyeb, Fly, Railway)
kini **mewajibkan kartu kredit untuk verifikasi**. Kartu user di-decline oleh
Stripe (bank Indonesia memblokir transaksi internasional / kartu non-Visa).

**Keputusan:** hosting ditunda. Fokus pengembangan lokal dulu.

**Rencana yang sudah disiapkan (tinggal eksekusi saat kartu tersedia):**
- Oracle Cloud Always Free (VM 4 core/24GB) + DuckDNS + Caddy → script siap.
- GitHub Actions cron (`refresh-jobs.yml`) → "jam" eksternal untuk fetch berkala.
- Alternatif tanpa kartu (dengan trade-off tidur/cold-start): SnapDeploy / Railway.

Detail lengkap di `DEPLOYMENT.md`.

---

## 12. Rencana Pengembangan Selanjutnya

Lihat `PLAN.md` untuk detail. Ringkas prioritas:

1. **Reranker & kalibrasi skor** — gunakan data label (dikumpulkan manual user)
   untuk menaikkan kualitas ranking.
2. **Parsing CV lebih pintar** — field per-jabatan, handle format CV kompleks.
3. **Fitur produk** — detail lowongan (modal), filter/sort, statistik.
4. **Kualitas teknis** — test suite (pytest), retry, logging.
5. **Sumber tambahan** — LinkedIn (ToS ketat) / aggregator global.

**Pertanyaan terbuka untuk user:**
- Berat preferensi (default 65%) mau ditambah slider di UI?
- NER/ML: serius melatih model sendiri (butuh dataset berlabel, sulit dicari),
  atau cukup aturan yang baik?

---

## 13. Catatan Teknis & Jebakan (pembelajaran)

- **Python 3.14**: `pydantic>=2.11` wajib (yang lama gagal compile cp314).
- **SQLite datetime** disimpan naive — bandingkan pakai `datetime.now(utc).replace(tzinfo=None)`.
- **fastembed tidak normalisasi vektor** — harus manual.
- **Endpoint portal berubah-ubah** — pola adapter mengisolasi risiko.
- **Kalibrr abaikan param keyword** — selalu balik feed penuh (justru bagus untuk pool).
- **Karir build ID dinamis** — ambil dari halaman utama tiap fetch detail.

---

## 14. Repositori & Profil

- **Repo GitHub**: `https://github.com/Anggito007/jobmatch` (public)
- **Lokasi lokal**: `C:\Project\jobseeker-automation`
- **Hermes Project**: "JobMatch" (workspace terkelompok)
