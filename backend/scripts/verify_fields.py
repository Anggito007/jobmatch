"""Uji menyeluruh: apakah hasil mengikuti CV & preferensi, dan apakah tersebar?

Menjawab keluhan:
  1. "hasil sangat sedikit"          -> cek jumlah hasil & pool per bidang
  2. "CV editing tapi muncul IoT"    -> cek relevansi judul vs bidang CV
  3. "dominan di satu website"       -> cek sebaran sumber pada hasil
  4. "apakah lowongan terbaru"       -> cek tanggal posting

Jalankan (backend harus hidup):
    cd backend && .venv/Scripts/python -m scripts.verify_fields
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8000"
SAMPLES = Path(__file__).resolve().parents[2] / "samples"

# CV -> kata kunci yang HARUS muncul di judul hasil teratas (relevansi).
CASES = [
    ("video_editor", ["video", "editor", "motion", "creative", "design", "content"]),
    ("accountant", ["account", "finance", "tax", "audit", "akuntan", "keuangan"]),
    ("digital_marketing", ["marketing", "social", "content", "brand", "seo", "growth"]),
    ("graphic_designer", ["design", "graphic", "visual", "creative", "ui", "ux"]),
    ("iot_engineer", ["iot", "embedded", "engineer", "hardware", "electronic", "firmware"]),
    ("backend_engineer", ["backend", "engineer", "developer", "software", "programmer"]),
    ("data_analyst", ["data", "analyst", "analytics", "bi", "business intelligence"]),
]


def run(cv_key: str, preference: str = "") -> dict:
    path = SAMPLES / f"{cv_key}.txt"
    files = {"file": (path.name, path.read_bytes(), "text/plain")}
    data = {
        "preference": preference,
        "filters": "{}",
        "top_n": "20",
        "keywords": "",
        "location": "",
        "live": "true",
        "min_score": "0",
    }
    return httpx.post(f"{BASE}/api/match", files=files, data=data, timeout=600).json()


def main() -> int:
    print("=" * 96)
    print("UJI 1 — Apakah hasil mengikuti BIDANG CV? (tanpa preferensi)")
    print("=" * 96)
    problems: list[str] = []

    for cv_key, expect in CASES:
        try:
            d = run(cv_key)
        except Exception as e:
            print(f"\n[{cv_key}] ERROR: {e}")
            problems.append(f"{cv_key}: request gagal")
            continue

        matches = d.get("matches", [])
        live = d.get("live") or {}
        per_src = live.get("per_source", {}) if isinstance(live, dict) else {}
        by_src = d.get("results_by_source", {})

        # Hitung berapa judul teratas yang relevan dengan bidangnya.
        top10 = matches[:10]
        hits = sum(
            1 for m in top10
            if any(k in m["title"].lower() for k in expect)
        )
        ratio = hits / max(len(top10), 1)

        print(f"\n[{cv_key}]  hasil={len(matches)}  pool={d.get('pool_size')}  "
              f"live_fetch={live.get('fetched', 0)}  relevan_top10={hits}/{len(top10)} ({ratio:.0%})")
        print(f"   per_sumber_fetch: {per_src}")
        print(f"   per_sumber_hasil: {by_src}")
        for m in top10[:5]:
            print(f"     {m['score']*100:3.0f}% [{m['source']:10}] {m['title'][:52]}")

        if ratio < 0.5:
            problems.append(f"{cv_key}: hanya {ratio:.0%} judul teratas relevan")
        if len(matches) < 5:
            problems.append(f"{cv_key}: hasil terlalu sedikit ({len(matches)})")

    print("\n" + "=" * 96)
    print("UJI 2 — Apakah PREFERENSI mengalahkan CV? (CV editing + preferensi IoT)")
    print("=" * 96)
    d = run("video_editor", preference="IoT embedded ESP32 LoRa sensor")
    top = d.get("matches", [])[:6]
    iot_first = bool(top) and any(
        k in top[0]["title"].lower() for k in ["iot", "embedded", "firmware", "hardware", "electronic"]
    )
    print(f"  hasil={len(top)}  #1 = {top[0]['title'][:60] if top else '-'}")
    for m in top:
        print(f"     {m['score']*100:3.0f}% [{m['source']:10}] {m['title'][:52]}")
    print(f"  -> preferensi IoT menang: {'YA' if iot_first else 'TIDAK'}")
    if not iot_first:
        problems.append("preferensi IoT tidak mengalahkan CV video editing")

    print("\n" + "=" * 96)
    print("UJI 3 — Sebaran sumber & kesegaran")
    print("=" * 96)
    d = run("backend_engineer")
    by_src = d.get("results_by_source", {})
    total = sum(by_src.values()) or 1
    top_share = max(by_src.values()) / total if by_src else 0
    print(f"  sebaran sumber hasil: {by_src}")
    print(f"  sumber terbesar: {top_share:.0%} dari hasil")
    if top_share > 0.6:
        problems.append(f"satu sumber mendominasi hasil ({top_share:.0%})")

    dates = [m.get("posted_at", "") for m in d.get("matches", []) if m.get("posted_at")]
    print(f"  contoh tanggal posting: {dates[:6]}")
    print(f"  ada tanggal: {len(dates)}/{len(d.get('matches', []))}")

    print("\n" + "=" * 96)
    if problems:
        print(f"MASALAH DITEMUKAN ({len(problems)}):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("SEMUA UJI LULUS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
