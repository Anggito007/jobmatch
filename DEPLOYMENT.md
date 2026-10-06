# Deployment JobMatch — Oracle Cloud Always Free + Vercel

Arsitektur final (gratis Rp0):

```
Frontend (Next.js)   →  Vercel (gratis)
Backend (FastAPI)    →  Oracle Cloud Always Free VM (gratis selamanya, 24GB RAM)
                        + DuckDNS subdomain gratis + Caddy (HTTPS otomatis)
DB                   →  SQLite (di disk VM, persistent)
```

> **Kenapa perlu HTTPS di backend:** halaman Vercel itu HTTPS. Browser akan
> **memblokir** request dari halaman HTTPS ke `http://IP:8000` (mixed content).
> Makanya backend harus diberi HTTPS lewat DuckDNS + Caddy (script sudah disiapkan).

---

## Bagian 1 — Daftar Oracle Cloud (sekali, butuh kartu untuk verifikasi)

1. Buka https://www.oracle.com/cloud/free/ → **Start for free**
2. Isi data (negara, nama, email). Saat diminta **kartu debit/kredit**:
   - Ini hanya **verifikasi identitas** (hold ~$1 lalu dikembalikan). Selama
     kamu cuma pakai resource Always Free, **tidak akan pernah ditagih**.
3. Verifikasi email + akun siap. Proses bisa 5–15 menit.

---

## Bagian 2 — Buat VM (Ampere A1, 4 core / 24GB RAM — always free)

1. Masuk console: https://cloud.oracle.com → pilih region (mis. **Singapore**,
   sering masih ada stok A1; kalau penuh coba region lain).
2. Menu kiri → **Compute → Instances** → **Create instance**
3. Isi:
   - **Name**: `jobmatch`
   - **Image**: klik *Change image* → **Canonical Ubuntu 22.04** (atau 24.04)
   - **Shape**: klik *Change shape* → tab **Specialty and legacy** → pilih
     **Ampere → VM.Standard.A1.Flex** → set **OCPU = 4, Memory = 24 GB**
     (ini batas always-free). Kalau A1 habis, fallback: *AMD → VM.Standard.E2.1.Micro*
     (1GB RAM — cukup untuk backend, tapi lebih lambat).
4. **Networking**: biarkan *Create new VCN* default. Centang **Assign public IPv4 address**.
5. **SSH key**: pilih *Paste public keys* → tempel ini (sudah saya generate):

   ```
   ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIMz2Ykljkh8Rxg1wiN5sQqPs3l7LGzz8EDNpbfqP10oR anggito-jobmatch
   ```

6. **Create**. Tunggu instance **Running** → catat **Public IP Address**.

---

## Bagian 3 — Buka port 80 & 443 (HTTPS) di firewall VCN

1. Di halaman instance, klik nama **Virtual cloud network** (VCN) → **Subnets** →
   klik subnet default.
2. Klik **Security Lists** → **Default Security List** → **Add Ingress Rules**:
   - Source: `0.0.0.0/0`, Protocol: **TCP**, Destination port: **80** → Add
   - Source: `0.0.0.0/0`, Protocol: **TCP**, Destination port: **443** → Add
3. (Opsional, untuk tes tanpa HTTPS) tambah juga port **8000**.

---

## Bagian 4 — SSH masuk & jalankan setup (sekali)

Di terminal Windows (git-bash), ganti `<IP_VM>` dengan IP dari Bagian 2:

```bash
ssh -i ~/.ssh/jobmatch_oracle ubuntu@<IP_VM>
```

Setelah masuk, jalankan:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Anggito007/jobmatch/main/scripts/deploy_oracle.sh)"
```

Ini otomatis: install Python → clone repo → venv + dependensi → unduh model
(~470MB) → pasang service yang **selalu jalan** (systemd). Tunggu 5–10 menit.

Verifikasi:

```bash
sudo systemctl status jobmatch
curl http://localhost:8000/health
```

---

## Bagian 5 — Pasang HTTPS (DuckDNS + Caddy)

**5a. Buat subdomain gratis di https://www.duckdns.org** (login pakai akun
GitHub/Google), buat domain mis. `anggito-jobmatch`, catat **token**-nya.

**5b. Di VM** (masih dalam sesi SSH):

```bash
cd ~/jobmatch
DOMAIN=anggito-jobmatch.duckdns.org DUCKDNS_TOKEN=TOKEN-KAMU bash scripts/deploy_https.sh
```

Caddy akan otomatis dapat sertifikat HTTPS (Let's Encrypt). Verifikasi:

```bash
curl https://anggito-jobmatch.duckdns.org/health
```

Backend kamu sekarang live di `https://anggito-jobmatch.duckdns.org`.

---

## Bagian 6 — Deploy frontend ke Vercel

1. Buka https://vercel.com → **Login pakai GitHub** (akun Anggito007)
2. **Add New → Project** → **Import** repo `Anggito007/jobmatch`
3. **Root Directory**: ketik `frontend`
4. Framework terdeteksi **Next.js** — biarkan default
5. **Environment Variables** → tambah:
   - `NEXT_PUBLIC_API_URL` = `https://anggito-jobmatch.duckdns.org`
6. **Deploy** → frontend live di `https://jobmatch-xxx.vercel.app`

---

## Checklist selesai

- [ ] Oracle Cloud terdaftar + VM A1 jalan (punya Public IP)
- [ ] Port 80 & 443 dibuka di VCN
- [ ] `deploy_oracle.sh` sukses (`/health` balas OK di dalam VM)
- [ ] HTTPS jalan (DuckDNS + Caddy, `curl https://DOMAIN/health` OK dari laptop)
- [ ] Vercel deploy frontend, root dir `frontend`, env `NEXT_PUBLIC_API_URL` terisi
- [ ] Uji: buka URL Vercel dari HP → upload CV → hasil muncul

---

## Troubleshooting

| Masalah | Solusi |
|---|---|
| "Out of capacity" saat bikin A1 | Ganti region (Singapore/Osaka/Mumbai sering ada). Atau coba lagi jam berbeda — kapasitas A1 fluktuatif. |
| `ssh` connection refused | Port 22 harusnya terbuka default. Pastikan IP benar, instance Running. |
| Caddy gagal dapat sertifikat | Pastikan port 80 & 443 terbuka di VCN, dan domain DuckDNS sudah menunjuk ke IP VM. |
| Vercel tidak bisa fetch backend | Cek `NEXT_PUBLIC_API_URL` benar + backend `curl https://DOMAIN/health` OK. CORS sudah `*`. |
| Backend lambat pertama kali | Normal — model ~470MB dimuat ke RAM saat start. Setelah itu cepat. |
