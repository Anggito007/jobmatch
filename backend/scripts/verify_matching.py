"""Verifikasi end-to-end: CV → fetch → embed → score → urutkan.

Run:
    python -m scripts.verify_matching
"""
from app.cv.profile import build_profile
from app.fetchers.glints import GlintsFetcher
from app.fetchers.jobstreet import JobStreetFetcher
from app.matching.embedder import get_embedder
from app.matching.scorer import job_skills, job_text, score_match

TEST_CV = """
Nama: Anggito Alif Abimanyu
Posisi: Backend Engineer
Skills: Python, FastAPI, PostgreSQL, Docker, IoT, LoRa, ESP32, REST API
Pengalaman: 2 tahun membangun backend dengan Python dan FastAPI,
merancang sistem monitoring IoT berbasis LoRa dan ESP32.
"""


def main() -> None:
    profile = build_profile(TEST_CV)
    print(f"Skills CV terdeteksi ({len(profile.skills)}): {profile.skills}\n")

    emb = get_embedder()
    cv_vec = emb.embed_one(profile.embedding_text)

    jobs = (
        JobStreetFetcher().fetch(["backend", "engineer"], location="Bandung")
        + GlintsFetcher().fetch(["backend", "engineer"])
    )
    print(f"{len(jobs)} lowongan difetch\n")

    texts = [job_text(j) for j in jobs]
    vecs = emb.encode(texts)

    results = []
    for job, jvec in zip(jobs, vecs):
        jskills = job_skills(job)
        score, matched = score_match(cv_vec, jvec, profile.skills, jskills)
        results.append((score, matched, job))

    results.sort(key=lambda r: r[0], reverse=True)

    print("=== TOP 10 MATCH ===")
    for score, matched, job in results[:10]:
        print(f"  {score:.3f}  [{job.source}] {job.title} @ {job.company}")
        if matched:
            print(f"         skill cocok: {', '.join(matched)}")
        print(f"         {job.url}")


if __name__ == "__main__":
    main()
