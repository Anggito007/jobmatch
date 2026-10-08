"""Verifikasi filter preferensi — tes regresi untuk bug "hasil terlalu sedikit".

Bug yang dijaga tes ini:
    Hard filter dulu membuang lowongan yang datanya KOSONG (92% work_arrangement
    kosong, 74% job_type kosong, 76% tanpa gaji). Akibatnya filter "Remote"
    menyusutkan pool 1.877 → 33, dan lowongan yang cocok dengan preferensi ikut
    terbuang sehingga hasil terlihat "tidak mengikuti preferensi".

Prinsip yang diuji: filter HANYA membuang lowongan bila datanya benar-benar
BERTENTANGAN. Data kosong = tidak diketahui = tetap lolos.

Jalankan (backend harus hidup di :8000):
    cd backend && .venv/Scripts/python -m scripts.verify_preferences
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8000"
# samples/ ada di root repo, sedangkan skrip ini dijalankan dari backend/.
CV = str(Path(__file__).resolve().parents[2] / "samples" / "iot_engineer.txt")
PREF = "IoT embedded ESP32 LoRa"
EXPECTED_TOP = "IoT"  # judul lowongan yang harus jadi #1 saat preferensi IoT aktif

# (label, filters, ambang minimum pool yang harus bertahan)
SCENARIOS = [
    ("tanpa filter", {}, 1800),
    ("Remote ON", {"remote": True}, 1000),
    ("Gaji min 5jt", {"min_salary": 5_000_000}, 1000),
    ("Full-time", {"job_types": ["full_time"]}, 1000),
    ("Spesialisasi Engineering", {"specializations": ["engineering"]}, 1500),
    ("Pendidikan S1", {"education_levels": ["bachelor"]}, 1500),
    ("Level Junior", {"position_levels": ["junior"]}, 1000),
]

failures: list[str] = []


def run(filters: dict) -> dict:
    with open(CV, "rb") as fh:
        files = {"file": ("cv.txt", fh.read(), "text/plain")}
    data = {
        "preference": PREF,
        "filters": json.dumps(filters),
        "top_n": "5",
        "keywords": "",
        "location": "",
    }
    return httpx.post(f"{BASE}/api/match", files=files, data=data, timeout=180).json()


def main() -> int:
    for label, filters, min_pool in SCENARIOS:
        d = run(filters)
        pool, top = d["pool_size"], d["matches"][0]["title"] if d["matches"] else ""
        ok_pool = pool >= min_pool
        ok_top = EXPECTED_TOP.lower() in top.lower()
        status = "OK  " if (ok_pool and ok_top) else "GAGAL"
        print(
            f"[{status}] {label:28} pool={pool:5} (min {min_pool})  "
            f"filtered_out={d.get('filtered_out', 0):5}  #1={top[:44]!r}"
        )
        if not ok_pool:
            failures.append(f"{label}: pool {pool} < {min_pool} — filter terlalu agresif")
        if not ok_top:
            failures.append(f"{label}: peringkat #1 {top!r} tidak mengikuti preferensi")

    print()
    if failures:
        print(f"GAGAL — {len(failures)} masalah:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"SEMUA LULUS — {len(SCENARIOS)} skenario, preferensi dihormati & pool tidak runtuh.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
