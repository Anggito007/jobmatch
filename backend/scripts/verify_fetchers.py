"""Smoke test: jalankan fetcher terhadap API asli dan cetak hasilnya.

Run:
    python -m scripts.verify_fetchers
"""
from app.fetchers.glints import GlintsFetcher
from app.fetchers.jobstreet import JobStreetFetcher


def main() -> None:
    keywords = ["backend engineer"]

    print("=== JobStreet ===")
    js_jobs = JobStreetFetcher().fetch(keywords, location="Bandung")
    print(f"  {len(js_jobs)} lowongan")
    for j in js_jobs[:5]:
        print(f"  - [{j.company}] {j.title} @ {j.location} ({j.work_arrangement})")
        print(f"    {j.url}")

    print("\n=== Glints ===")
    gl_jobs = GlintsFetcher().fetch(keywords)
    print(f"  {len(gl_jobs)} lowongan")
    for j in gl_jobs[:5]:
        salary = ""
        if j.salary_max:
            salary = f"  Rp{j.salary_min:,.0f}-{j.salary_max:,.0f}".replace(",", ".")
        print(f"  - [{j.company}] {j.title} @ {j.location}{salary}")
        print(f"    {j.url}")


if __name__ == "__main__":
    main()
