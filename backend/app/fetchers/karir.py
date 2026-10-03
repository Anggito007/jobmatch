"""Karir.com fetcher — public gateway API (POST)."""
from __future__ import annotations

import httpx

from .base import BaseFetcher, Job

API_URL = "https://gateway2-beta.karir.com/v2/search/opportunities"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Origin": "https://karir.com",
    "Referer": "https://karir.com/",
}


class KarirFetcher(BaseFetcher):
    source_name = "karir"

    def fetch(
        self,
        keywords: list[str],
        location: str = "",
        page_size: int = 10,
        max_pages: int = 15,
    ) -> list[Job]:
        jobs: list[Job] = []
        # Karir pakai "*" untuk semua; kata kunci spesifik juga didukung.
        term = " ".join(keywords).strip() or "*"

        with httpx.Client(headers=HEADERS, timeout=30.0) as client:
            for page in range(max_pages):
                payload = {
                    "keyword": term,
                    "location_ids": [],
                    "company_ids": [],
                    "industry_ids": [],
                    "job_function_ids": [],
                    "degree_ids": [],
                    "locale": "id",
                    "limit": page_size,
                    "offset": page * page_size,
                    "level": "",
                    "min_employee": 0,
                    "max_employee": 50,
                    "is_opportunity": True,
                    "sort_order": "",
                    "is_recomendation": False,
                    "is_preference": False,
                    "is_choice_opportunity": False,
                    "is_subscribe": False,
                    "workplace": None,
                }
                resp = client.post(API_URL, json=payload)
                resp.raise_for_status()
                body = resp.json()
                data = body.get("data") or {}
                items = data.get("opportunities") or []
                if not items:
                    break
                jobs.extend(self._parse(i) for i in items)
        return jobs

    @staticmethod
    def _parse(i: dict) -> Job:
        job_id = i.get("id")
        return Job(
            source="karir",
            external_id=str(job_id),
            title=i.get("job_position", ""),
            company=i.get("company_name", ""),
            location=(i.get("description") or "").split("•")[0].strip(),
            salary_min=i.get("salary_lower"),
            salary_max=i.get("salary_upper"),
            url=f"https://karir.com/opportunities/{job_id}",
            posted_at=i.get("posted_at", ""),
        )
