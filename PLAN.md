# JobMatch — Rencana Pengembangan Lanjutan

Status: backend + frontend MVP jalan, 6 sumber lowongan, matching semantik,
auth, save/feedback, email digest. Hosting ditunda (lihat DEPLOYMENT.md).

Prioritas disusun berdasarkan dampak nyata ke kualitas & kelayakan produk,
bukan kemudahan implementasi.

---

## PRIORITAS 1 — Kualitas matching (paling berdampak)

Masalah nyata yang sudah terlihat dari pengujian: beberapa sumber (Glints,
Kalibrr, Karir, Dealls) hanya memberi JUDUL tanpa deskripsi lengkap, sehingga
embedding-nya dangkal dan skor jadi bias. Lowongan dari TechInAsia (punya
deskripsi penuh) otomatis lebih mendominasi hasil.

### 1.1 Ambil deskripsi lowongan lengkap
- Glints: temukan query GraphQL detail job (field deskripsi belum ketemu) ATAU
  scrape halaman `glints.com/id/opportunities/jobs/<id>`.
- Kalibrr, Karir, Dealls: fetch halaman detail per job untuk ambil deskripsi.
- Efek: embedding jauh lebih akurat, semua sumber setara.

### 1.2 Reranker (naikkan kualitas ranking)
- Saat ini skor = 0.45·cosine + 0.30·skill + 0.25·lexical (bobot manual).
- Tingkatkan: gunakan data feedback 👍/👎 yang sudah terkumpul untuk melatih
  reranker sederhana, atau paling tidak jadikan feedback mempengaruhi ranking
  (job yang sering 👎 ditekan bobotnya).

### 1.3 Kalibrasi skor per sumber
- Normalisasi supaya satu sumber tidak mendominasi top-N hanya karena deskripsi
  panjang. Cek distribusi skor per sumber, tambah normalisasi bila timpang.

---

## PRIORITAS 2 — Parsing CV lebih pintar

### 2.1 Ekstrak lebih banyak field
- Perusahaan & jabatan tiap pengalaman kerja.
- Tahun mulai-selesai (sudah ada total, belum per-jabatan).
- IPK, skill level (beginner/intermediate/advanced) kalau tertulis.

### 2.2 Handle format CV yang berantakan
- CV PDF yang pakai kolom (dua kolom), tabel, atau layout kompleks sering gagal
  diekstrak rapi. Uji dengan beberapa CV asli, perbaiki extractor.

### 2.3 (Opsional) NER dengan model
- Kalau mau "pakai ML lebih dalam" untuk portofolio: fine-tune model kecil
  (XLM-R) untuk deteksi skill/jabatan/pendidikan dari CV Indonesia. Butuh
  dataset berlabel (bisa dibangun dari feedback + CV sampel).

---

## PRIORITAS 3 — Fitur produk

### 3.1 Detail lowongan
- Klik kartu → halaman/modal detail: deskripsi penuh, requirements, tombol apply.

### 3.2 Riwayat & statistik
- Grafik tren: jumlah lowongan baru per minggu, per sumber, per kategori.
- (Bagus untuk portofolio — ada visualisasi.)

### 3.3 Filter & sort di dashboard
- Filter lokasi, sumber, jenis pekerjaan, rentang gaji.
- Sort: skor / tanggal / gaji.

### 3.4 Notifikasi (lanjutan)
- Email digest sudah ada tapi belum diaktifkan SMTP. Tambah: Telegram bot
  (opsional, user minta) bila mau.

---

## PRIORITAS 4 — Kualitas & teknis

### 4.1 Tes otomatis
- Belum ada test suite. Tambah pytest untuk: ekstraksi skill, scoring, fetcher
  parser (pakai fixture JSON), auth.

### 4.2 Error handling & retry
- Fetcher kadang gagal (rate limit, timeout). Tambah retry + fallback.

### 4.3 Observability
- Logging terstruktur, metrik sederhana (berapa job difetch, berapa gagal).

---

## PRIORITAS 5 — Sumber tambahan (setelah inti stabil)

- LinkedIn (opsional, ToS ketat — perlu Playwright + rate rendah).
- Aggregator global (Jooble/Adzuna) bila mau cakupan internasional.
- Sumber niche Indonesia lain: Karirpad, Urbanhire, dsb. (evaluasi dulu API-nya).

---

## Yang TIDAK saya sarankan sekarang

- Deploy (ditunda — kamu yang minta).
- Auth sosial (Google/GitHub OAuth) — belum perlu, auth email cukup.
- Pindah ke microservices — overkill untuk tahap ini.
- ML model raksasa (BERT-large, LLM untuk matching) — biaya & latensi tidak
  sebanding dengan manfaat di tahap ini.

---

## Urutan eksekusi yang saya rekomendasikan

1. **1.1** (deskripsi lengkap) — karena ini yang paling besar efeknya ke akurasi,
   dan sudah ketahuan masalahnya dari uji coba.
2. **4.1** (test) — sebelum fitur makin banyak, kunci dulu perilaku yang sudah benar.
3. **1.2 + 1.3** (reranker + kalibrasi) — pakai data feedback.
4. **2.1 + 2.2** (parsing CV) — biar tahan CV format macam-macam.
5. **3.1 + 3.3** (detail + filter) — polish UX.
6. **3.2** (statistik) — bahan portofolio.

---

## Open questions untuk user

1. Prioritas utama: akurasi matching dulu, atau fitur UX (detail/filter) dulu?
2. Feedback 👍/👎 mau dipakai untuk apa: sekadar tombol, atau beneran mempengaruhi
   ranking & jadi data training reranker?
3. Untuk 2.3 (NER/ML), kamu mau serius melatih model sendiri (untuk nilai
   portofolio), atau cukup aturan/regex yang baik?
