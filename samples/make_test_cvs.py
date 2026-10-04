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
