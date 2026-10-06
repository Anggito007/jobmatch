"""Dealls fetcher — public JSON API (api.sejutacita.id).

Endpoint yang dipakai frontend dealls.com sendiri; tanpa auth.
"""
from __future__ import annotations

import httpx

from .base import BaseFetcher, Job

API_URL = "https://api.sejutacita.id/v1/explore-job/job"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://dealls.com",
    "Referer": "https://dealls.com/",
}


class DeallsFetcher(BaseFetcher):
    source_name = "dealls"

    def fetch(
        self,
        keywords: list[str],
        location: str = "",
        page_size: int = 15,
        max_pages: int = 5,
    ) -> list[Job]:
        jobs: list[Job] = []

        with httpx.Client(headers=HEADERS, timeout=30.0) as client:
            for page in range(1, max_pages + 1):
                params = {
                    "page": page,
                    "sortParam": "mostRelevant",
                    "sortBy": "asc",
                    "published": "true",
                    "limit": page_size,
                    "status": "active",
                }
                # API Dealls tidak punya param keyword — ini feed "most relevant".
                # Relevance diserahkan ke semantic matching (bukan filter keyword).
                resp = client.get(API_URL, params=params)
                resp.raise_for_status()
                docs = ((resp.json().get("data") or {}).get("docs")) or []
                if not docs:
                    break
                jobs.extend(self._parse(d) for d in docs)
        return jobs

    @staticmethod
    def _parse(d: dict) -> Job:
        company = d.get("company") or {}
        city = d.get("city") or {}
        slug = d.get("slug", "")
        salary_range = d.get("salaryRange") or {}
        # skills berupa list of dict {name: ...}.
        skills = [s["name"] for s in (d.get("skills") or []) if isinstance(s, dict) and s.get("name")]
        return Job(
            source="dealls",
            external_id=str(d.get("id", "")),
            title=d.get("role", ""),
            company=company.get("name", ""),
            location=city.get("name", ""),
            salary_min=salary_range.get("start"),
            salary_max=salary_range.get("end"),
            job_type=", ".join(d.get("employmentTypes") or []),
            work_arrangement=d.get("workplaceType", ""),
            skills=skills,
            url=f"https://dealls.com/role/{slug}",
            posted_at=d.get("publishedAt", ""),
        )


if __name__ == "__main__":
    print(len(DeallsFetcher().fetch(["backend"])))
