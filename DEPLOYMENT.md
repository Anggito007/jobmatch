# Deployment JobMatch — Langkah Konkret

## Ringkasan arsitektur final

```
Frontend (Next.js)   →  Vercel (gratis)
Backend (FastAPI)    →  HF Spaces / VPS / Render  (BUKAN Vercel — torch+model ~1GB)
DB (Postgres)        →  Neon / Supabase (gratis)  [opsional, SQLite cukup untuk demo]
```

**Kenapa backend tidak di Vercel:** backend butuh proses yang selalu jalan
(scheduler), model ML ~470MB, dan torch ~500MB — total ~1GB. Vercel serverless
punya durasi & ukuran terbatas, tidak bisa menjalankan ini.

---

## Langkah 1 — Push kode ke GitHub

### 1a. Siapkan token (sekali)
1. Buka https://github.com/settings/tokens → **Generate new token (classic)**
2. Nama: `hermes-agent` · Expiration: 90 hari
3. Centang scope **`repo`** (dan `workflow` kalau mau CI)
4. **Copy token** (tidak akan ditampilkan lagi)

### 1b. Buat repo + push
Di terminal (folder `C:\Hermes\jobseeker-automation`):

```bash
git config user.name "NamaKamu"
git config user.email "email@kamu.com"

# Buat repo kosong dulu di github.com (jangan centang "Add README")
# atau lewat CLI kalau gh sudah terinstall:
# gh repo create jobmatch --public --source . --push

git remote add origin https://github.com/USERNAME/jobmatch.git
git push -u origin main
```

Saat diminta password: isi **token** (bukan password GitHub).

---

## Langkah 2 — Deploy frontend ke Vercel

### Cara termudah (GUI, tanpa CLI):

1. Buka https://vercel.com → **Login** (pakai akun GitHub biar sekalian nyambung)
2. Klik **Add New → Project** → **Import** repo `jobmatch`
3. **PENTING**: di **Root Directory**, ketik `frontend` (karena repo punya `backend/` juga)
4. Framework otomatis terdeteksi **Next.js** — biarkan default
5. **Environment Variables** → tambahkan:
   - `NEXT_PUBLIC_API_URL` = `https://<URL-BACKEND-KAMU>` (dari Langkah 3)
6. Klik **Deploy**

Selesai deploy, frontend live di `https://jobmatch-xxx.vercel.app`.

> ⚠️ Tanpa `NEXT_PUBLIC_API_URL` yang benar, tombol "Cari Lowongan" akan gagal
> (karena default-nya `http://localhost:8000`).

---

## Langkah 3 — Deploy backend (pilih satu)

### Opsi A — Hugging Face Spaces (gratis, paling pas untuk ML, ~0 biaya)

1. Buka https://huggingface.co/spaces → **Create new Space**
2. Pilih **Docker** SDK, Public
3. Upload isi folder `backend/` (atau hubungkan ke repo GitHub)
4. HF Spaces free tier: 2 vCPU, 16GB RAM, 50GB disk → backend muat nyaman
5. Setelah jalan, URL backend = `https://<user>-jobmatch.hf.space`
6. Isi `NEXT_PUBLIC_API_URL` di Vercel dengan URL itu, lalu re-deploy

Catatan: HF Spaces punya *cold start* (bangun ~1-2 menit saat pertama diakses
setelah idle). Untuk portofolio/demo tidak masalah.

### Opsi B — VPS murah (paling stabil, ~Rp50-100rb/bln)

1. Sewa VPS (Contabo/IDCloudHost/DigitalOcean droplet termurah)
2. Install Docker, jalankan `backend/Dockerfile`
3. Pasang HTTPS (Caddy/nginx + Let's Encrypt)
4. URL backend = domain/subdomain VPS kamu

### Opsi C — Render free tier (perlu mengecilkan backend dulu)

Render free = 512MB disk, backend ~1GB tidak muat. Supaya muat:
- Ganti `sentence-transformers` → `fastembed` (ONNX, runtime lebih kecil), ATAU
- Pakai embedding API ([OI] `text-embedding-3-small` / Gemini), backend jadi <200MB.

Setelah dikecilkan, deploy pakai `backend/render.yaml` (blueprint), set
`CORS_ORIGINS` = URL Vercel, `DATABASE_URL` = Postgres Neon.

---

## Langkah 4 — Set env var di Vercel (rekap)

| Var | Nilai |
|---|---|
| `NEXT_PUBLIC_API_URL` | URL backend publik (HF Spaces / VPS / Render) |

Dan di backend, pastikan CORS mengizinkan origin Vercel:
`CORS_ORIGINS=https://jobmatch-xxx.vercel.app` (di `.env` backend / env host).

---

## Checklist selesai

- [ ] Kode ter-push ke GitHub (repo publik untuk portofolio)
- [ ] Frontend live di Vercel, root dir `frontend`, env `NEXT_PUBLIC_API_URL` terisi
- [ ] Backend live (HF Spaces / VPS), CORS di-allow
- [ ] Uji: buka URL Vercel dari HP orang lain → upload CV → hasil muncul
