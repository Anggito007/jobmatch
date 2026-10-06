"""Kalibrr fetcher — public JSON endpoint (limit sampai 2000/page)."""
from __future__ import annotations

import httpx

from .base import BaseFetcher, Job
from .utils import strip_html

API_URL = "https://www.kalibrr.com/kjs/job_board/search"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


class KalibrrFetcher(BaseFetcher):
    source_name = "kalibrr"

    def fetch(
        self,
        keywords: list[str],
        location: str = "",
        page_size: int = 2000,
        max_pages: int = 1,
    ) -> list[Job]:
        # Kalibrr mengabaikan param keyword (q) — selalu balik feed penuh (~1200
        # job aktif). Itu justru bagus untuk pool matching yang beragam.
        jobs: list[Job] = []
        term = " ".join(keywords)

        with httpx.Client(headers=HEADERS, timeout=30.0) as client:
            for page in range(max_pages):
                params = {"limit": page_size, "offset": page * page_size}
                if term:
                    params["q"] = term
                if location:
                    params["location"] = location
                resp = client.get(API_URL, params=params)
                resp.raise_for_status()
                items = resp.json().get("jobs") or []
                if not items:
                    break
                jobs.extend(self._parse(i) for i in items)
        return jobs

    @staticmethod
    def _parse(i: dict) -> Job:
        company = i.get("company") or {}
        code = company.get("code", "")
        job_id = i.get("id", "")
        # Kalibrr search sudah menyertakan deskripsi & kualifikasi lengkap (HTML).
        desc = strip_html(i.get("description")) or strip_html(i.get("summary"))
        quals = strip_html(i.get("qualifications"))
        requirements = " ".join(x for x in [quals] if x)
        return Job(
            source="kalibrr",
            external_id=str(job_id),
            title=i.get("name", ""),
            company=company.get("name", ""),
            location=i.get("location", ""),
            salary_min=i.get("base_salary"),
            salary_max=i.get("maximum_salary"),
            description=desc,
            requirements=requirements,
            job_type=(i.get("employment_type") or {}).get("name", "")
            if isinstance(i.get("employment_type"), dict)
            else "",
            url=f"https://www.kalibrr.com/c/{code}/jobs/{job_id}",
            posted_at=i.get("activation_date", ""),
        )
