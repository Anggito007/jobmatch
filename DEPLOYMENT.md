# Deployment JobMatch

## Kendala utama: ukuran backend vs free tier

Backend butuh:
- torch (CPU): ~500MB terinstall
- model embedding `paraphrase-multilingual-MiniLM-L12-v2`: ~470MB
- **Total ~1GB**

Free tier yang umum:
| Layanan | Disk | RAM | Muat? |
|---|---|---|---|
| Render free | 512MB | 512MB | ❌ tidak |
| Railway free | ~500MB (trial) | 512MB | ❌ tidak |
| Fly.io free (legacy) | 1-3GB volume | 256MB | ⚠️ mepet |
| **VPS murah** (IDCloudHost/Contabo) | 20-40GB | 1-2GB | ✅ |

## Rekomendasi urutan

1. **Lokal / demo**: jalan di laptop (sudah jalan).
2. **Portofolio live yang murah & stabil**: VPS murah (~Rp50-100rb/bln) — muat semua.
3. **Mau tetap gratis penuh**: ganti embedder ke yang lebih ringan:
   - `fastembed` (ONNX, ~50MB runtime + model `BAAI/bge-small-en-v1.5` ~130MB,
     atau multilingual `intfloat/multilingual-e5-small` ~470MB) → masih mepet
   - atau pakai embedding API (OpenAI `text-embedding-3-small` / Gemini) → backend
     jadi ringan (<200MB), muat di Render free. Tapi ada biaya API per request.

## Arsitektur final

```
Frontend (Next.js)  →  Vercel (gratis, tanpa batas disk bermasalah)
Backend (FastAPI)   →  Render free / Railway / VPS (tergantung pilihan embedder)
DB (Postgres)       →  Neon / Supabase (gratis)
```

## Langkah deploy (nanti di Fase 3)

1. `git push` ke GitHub (repo publik untuk portofolio).
2. Frontend: import repo ke Vercel → detect Next.js → deploy otomatis.
3. Backend: import repo ke Render (pakai `render.yaml`) ATAU deploy ke VPS.
4. Set `CORS_ORIGINS` backend = URL frontend Vercel.
5. Set `DATABASE_URL` backend = Postgres Neon/Supabase.
