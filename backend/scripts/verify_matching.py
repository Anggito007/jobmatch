"""Verifikasi end-to-end: collect broad → skor CV vs pool DB → urutkan.

Run:
    python -m scripts.verify_matching
"""
from app.cv.profile import build_profile
from app.db import init_db
from app.matching.embedder import get_embedder
from app.matching.scorer import job_skills, job_text, score_match
from app.scheduler import collect_jobs
from app.store import get_jobs

TEST_CV = """
Nama: Anggito Alif Abimanyu
Posisi: Backend Engineer
Skills: Python, FastAPI, PostgreSQL, Docker, IoT, LoRa, ESP32, REST API
Pengalaman: 2 tahun membangun backend dengan Python dan FastAPI,
merancang sistem monitoring IoT berbasis LoRa dan ESP32.
"""


def main() -> None:
    init_db()
    profile = build_profile(TEST_CV)
    print(f"Skills CV ({len(profile.skills)}): {profile.skills}\n")

    emb = get_embedder()
    cv_vec = emb.embed_one(profile.embedding_text)

    # Kumpulkan pool broad (jika DB kosong).
    rows = get_jobs(limit=5000)
    if not rows:
        print("DB kosong — collect broad...")
        print(collect_jobs())
        rows = get_jobs(limit=5000)
    sources = {r.source for r in rows}
    print(f"Pool: {len(rows)} lowongan dari {len(sources)} sumber {sorted(sources)}\n")

    results = []
    for row in rows:
        jtext = job_text(row)
        jvec = row.embedding or emb.embed_one(jtext)
        jskills = row.skills or job_skills(row)
        score, matched = score_match(
            cv_vec, list(jvec), profile.skills, jskills,
            cv_text=profile.embedding_text, job_text_str=jtext,
        )
        results.append((score, matched, row))

    results.sort(key=lambda r: r[0], reverse=True)

    print("=== TOP 15 MATCH (semua sumber) ===")
    for score, matched, row in results[:15]:
        print(f"  {score:.3f}  [{row.source}] {row.title} @ {row.company}")
        if matched:
            print(f"         skill cocok: {', '.join(matched)}")
        print(f"         {row.url}")


if __name__ == "__main__":
    main()
