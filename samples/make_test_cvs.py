"""Generate 3 CV sampel (.docx + .txt) untuk pengujian matching.

Run:
    python samples/make_test_cvs.py
"""
from pathlib import Path

import docx

OUT = Path(__file__).parent

CVS = {
    "backend_engineer": {
        "nama": "Rizky Pratama",
        "teks": """RIZKY PRATAMA
Backend Engineer
rizky.pratama@email.com | +62 812-3456-7890 | Jakarta

RINGKASAN
Backend Engineer dengan 6 tahun pengalaman membangun API, microservices, dan sistem pembayaran berskala tinggi. Terbiasa dengan Python dan Go, serta infrastruktur cloud.

KEAHLIAN
Python, Go, FastAPI, Django, PostgreSQL, MySQL, Redis, Docker, Kubernetes, AWS, REST API, gRPC, CI/CD, Git, Linux

PENGALAMAN
PT Nusantara Teknologi (2022 - sekarang)
Backend Engineer
- Merancang layanan pembayaran yang menangani 1 juta transaksi per hari
- Optimasi query PostgreSQL dan caching Redis menurunkan latensi 40%
- Menulis CI/CD pipeline dan deploy ke Kubernetes di AWS

PT Digital Kreatif (2020 - 2022)
Software Engineer
- Membangun REST API dengan Python dan FastAPI untuk aplikasi mobile
- Integrasi payment gateway dan notifikasi

PENDIDIKAN
S1 Teknik Informatika, Universitas Indonesia (2016 - 2020)""",
    },
    "data_analyst": {
        "nama": "Dewi Lestari",
        "teks": """DEWI LESTARI
Data Analyst
dewi.lestari@email.com | +62 813-9876-5432 | Bandung

RINGKASAN
Data Analyst dengan 5 tahun pengalaman mengolah data menjadi insight bisnis. Ahli dalam visualisasi data dan pembuatan dashboard.

KEAHLIAN
SQL, Python, Pandas, NumPy, Power BI, Tableau, Google BigQuery, ETL, Data Visualization, Statistics, Excel, Data Analysis

PENGALAMAN
PT Retail Sejahtera (2022 - sekarang)
Data Analyst
- Membangun dashboard penjualan harian dengan Power BI untuk 50 toko
- Forecasting penjualan bulanan dengan Python (Pandas, NumPy)
- ETL data dari berbagai sumber ke BigQuery

Startup Analitik (2021 - 2022)
Junior Data Analyst
- Analisis data pelanggan untuk kampanye marketing
- Laporan mingguan dengan Tableau

PENDIDIKAN
S1 Statistika, Universitas Padjadjaran (2017 - 2021)""",
    },
    "iot_engineer": {
        "nama": "Budi Santoso",
        "teks": """BUDI SANTOSO
IoT Engineer
budi.santoso@email.com | +62 811-2233-4455 | Yogyakarta

RINGKASAN
IoT Engineer dengan 5 tahun pengalaman membangun sistem monitoring berbasis sensor, LoRa, dan ESP32 untuk sektor pertanian dan industri.

KEAHLIAN
C, C++, Python, ESP32, Arduino, LoRa, MQTT, Raspberry Pi, Embedded, Sensor, Microcontroller, PCB Design, IoT

PENGALAMAN
PT Agro Teknologi (2022 - sekarang)
IoT Engineer
- Merancang sistem monitoring hidroponik berbasis ESP32 dan LoRa untuk 20 greenhouse
- Pengiriman data sensor (suhu, kelembaban, pH) via MQTT ke server
- Desain PCB untuk node sensor bertenaga baterai

CV Karya Mandiri (2021 - 2022)
Embedded Developer
- Firmware Arduino dan ESP32 untuk alat ukur industri
- Integrasi sensor dan aktuator

PENDIDIKAN
S1 Teknik Komputer, Universitas Komputer Indonesia (2017 - 2021)""",
    },
    "video_editor": {
        "nama": "Andi Nugroho",
        "teks": """ANDI NUGROHO
Video Editor & Motion Designer
andi.nugroho@email.com | +62 815-4433-2211 | Jakarta

RINGKASAN
Video Editor dengan 4 tahun pengalaman mengedit konten untuk media sosial, iklan, dan YouTube. Terbiasa menangani alur produksi dari rough cut sampai color grading.

KEAHLIAN
Adobe Premiere Pro, After Effects, DaVinci Resolve, Motion Graphics, Color Grading, Video Editing, Sound Design, CapCut, Final Cut Pro, Storyboard, Videografi, Animasi 2D

PENGALAMAN
Kreatif Studio Digital (2022 - sekarang)
Video Editor
- Mengedit 40+ video iklan dan konten media sosial setiap bulan
- Motion graphics dengan After Effects untuk kampanye brand
- Color grading dengan DaVinci Resolve untuk video komersial

Agency Kreatif Nusantara (2021 - 2022)
Junior Video Editor
- Rough cut dan fine cut untuk konten YouTube klien
- Menyusun storyboard bersama tim kreatif

PENDIDIKAN
S1 Desain Komunikasi Visual, Institut Kesenian Jakarta (2017 - 2021)""",
    },
    "accountant": {
        "nama": "Siti Rahayu",
        "teks": """SITI RAHAYU
Accounting Staff
siti.rahayu@email.com | +62 812-7788-9900 | Surabaya

RINGKASAN
Accounting Staff dengan 5 tahun pengalaman menangani jurnal, rekonsiliasi bank, pelaporan pajak, dan penyusunan laporan keuangan bulanan.

KEAHLIAN
Akuntansi, Rekonsiliasi Bank, Pajak PPh, PPN, e-Faktur, Laporan Keuangan, Accurate, MYOB, Excel, Jurnal Umum, Audit, Akuntansi Biaya

PENGALAMAN
PT Manufaktur Sejahtera (2021 - sekarang)
Accounting Staff
- Menyusun laporan keuangan bulanan dan tahunan
- Rekonsiliasi bank dan penanganan e-Faktur pajak
- Akuntansi biaya produksi dengan Accurate

Kantor Akuntan Publik (2019 - 2021)
Junior Auditor
- Audit laporan keuangan klien manufaktur dan dagang

PENDIDIKAN
S1 Akuntansi, Universitas Airlangga (2015 - 2019)""",
    },
    "digital_marketing": {
        "nama": "Putri Anggraini",
        "teks": """PUTRI ANGGRAINI
Digital Marketing Specialist
putri.anggraini@email.com | +62 813-1122-3344 | Bandung

RINGKASAN
Digital Marketing Specialist dengan 4 tahun pengalaman mengelola kampanye media sosial, SEO, dan iklan berbayar dengan fokus pada pertumbuhan penjualan online.

KEAHLIAN
Digital Marketing, SEO, SEM, Google Ads, Meta Ads, Social Media Marketing, Content Marketing, Copywriting, Google Analytics, Email Marketing, Branding, TikTok Ads

PENGALAMAN
E-commerce Fashion Lokal (2022 - sekarang)
Digital Marketing Specialist
- Mengelola budget iklan Google dan Meta Ads Rp 150 juta/bulan
- Meningkatkan trafik organik 180% lewat strategi SEO konten
- Kampanye TikTok untuk peluncuran produk baru

Startup EdTech (2021 - 2022)
Marketing Executive
- Social media marketing dan email marketing
- Analisis performa kampanye dengan Google Analytics

PENDIDIKAN
S1 Ilmu Komunikasi, Universitas Padjadjaran (2017 - 2021)""",
    },
    "graphic_designer": {
        "nama": "Bayu Setiawan",
        "teks": """BAYU SETIAWAN
Graphic Designer
bayu.setiawan@email.com | +62 811-5566-7788 | Yogyakarta

RINGKASAN
Graphic Designer dengan 3 tahun pengalaman membuat identitas visual, materi promosi digital, dan desain antarmuka untuk brand lokal dan UMKM.

KEAHLIAN
Adobe Photoshop, Adobe Illustrator, Figma, CorelDRAW, Graphic Design, Branding, Logo Design, Typography, Layout Design, UI Design, Social Media Design, Canva

PENGALAMAN
Studio Desain Kreatif (2023 - sekarang)
Graphic Designer
- Merancang identitas visual dan logo untuk 30+ UMKM
- Desain materi promosi digital untuk media sosial
- Prototipe UI aplikasi mobile dengan Figma

Percetakan Digital (2022 - 2023)
Junior Designer
- Desain kemasan dan materi cetak

PENDIDIKAN
S1 Desain Komunikasi Visual, ISI Yogyakarta (2018 - 2022)""",
    },
}


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for key, cv in CVS.items():
        # .txt (mudah dibaca/direview)
        (OUT / f"{key}.txt").write_text(cv["teks"], encoding="utf-8")
        # .docx (realistis untuk upload)
        d = docx.Document()
        for line in cv["teks"].split("\n"):
            if line.strip():
                d.add_paragraph(line)
        d.save(str(OUT / f"{key}.docx"))
        print(f"✓ {key}.txt / {key}.docx  ({cv['nama']})")


if __name__ == "__main__":
    main()
