"""Glints fetcher — public GraphQL `searchJobsV3` + detail JSON-LD.

Search tidak menyertakan deskripsi (`descriptionJsonString` = null). Deskripsi
lengkap ada di halaman detail sebagai JSON-LD `JobPosting`. Maka setelah search,
kita fetch detail tiap job secara paralel untuk ambil description + skills.
"""
from __future__ import annotations

import json
import re

import httpx

from .base import BaseFetcher, Job
from .utils import fetch_many, strip_html

API_URL = "https://glints.com/api/v2-alc/graphql"

SEARCH_QUERY = """
query searchJobsV3($data: JobSearchConditionInput!) {
  searchJobsV3(data: $data) {
    jobsInPage {
      id
      title
      company { name }
      city { name }
      country { name }
      salaries { salaryType salaryMode minAmount maxAmount CurrencyCode }
      createdAt
    }
    hasMore
  }
}
"""

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    ),
    "Content-Type": "application/json",
    "Origin": "https://glints.com",
    "Referer": "https://glints.com/id/opportunities/jobs/explore",
}

_HTML_HEADERS = {
    "User-Agent": HEADERS["User-Agent"],
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
}


class GlintsFetcher(BaseFetcher):
    source_name = "glints"

    def fetch(
        self,
        keywords: list[str],
        location: str = "",
        country: str = "ID",
        page_size: int = 30,
        max_pages: int = 3,
        enrich: bool = True,
    ) -> list[Job]:
        jobs: list[Job] = []
        term = " ".join(keywords)

        with httpx.Client(headers=HEADERS, timeout=30.0) as client:
            for page in range(1, max_pages + 1):
                body = {
                    "operationName": "searchJobsV3",
                    "variables": {
                        "data": {
                            "SearchTerm": term,
                            "CountryCode": country,
                            "includeExternalJobs": True,
                            "pageSize": page_size,
                            "page": page,
                        }
                    },
                    "query": SEARCH_QUERY,
                }
                resp = client.post(API_URL, json=body)
                resp.raise_for_status()
                payload = resp.json()
                result = (payload.get("data") or {}).get("searchJobsV3") or {}
                items = result.get("jobsInPage") or []
                if not items:
                    break
                jobs.extend(self._parse(item) for item in items)
                if not result.get("hasMore"):
                    break

        # Enrich deskripsi dari halaman detail (JSON-LD) secara paralel.
        if enrich and jobs:
            self._enrich_details(jobs)
        return jobs

    def _enrich_details(self, jobs: list[Job], max_workers: int = 6) -> None:
        """Fetch halaman detail tiap job → ambil description + skills dari JSON-LD."""
        url_map = {j.url: j for j in jobs if j.url}
        pages = fetch_many(list(url_map.keys()), _HTML_HEADERS, max_workers=max_workers)
        for url, html in pages.items():
            if not html:
                continue
            data = _extract_jobposting(html)
            if not data:
                continue
            job = url_map[url]
            job.description = strip_html(data.get("description")) or job.description
            skills = data.get("skills")
            if isinstance(skills, list) and skills and not job.skills:
                job.skills = [s for s in skills if isinstance(s, str)]
            elif isinstance(skills, str) and skills and not job.skills:
                job.skills = [s.strip() for s in skills.split(",") if s.strip()]

    @staticmethod
    def _parse(item: dict) -> Job:
        salaries = item.get("salaries") or []
        salary = salaries[0] if salaries else {}
        city = (item.get("city") or {}).get("name")
        country = (item.get("country") or {}).get("name")
        job_id = str(item.get("id", ""))
        return Job(
            source="glints",
            external_id=job_id,
            title=item.get("title", ""),
            company=(item.get("company") or {}).get("name", ""),
            location=city or country or "",
            salary_min=salary.get("minAmount"),
            salary_max=salary.get("maxAmount"),
            currency=salary.get("CurrencyCode", "IDR"),
            url=f"https://glints.com/id/opportunities/jobs/{job_id}",
            posted_at=item.get("createdAt", ""),
        )


def _extract_jobposting(html: str) -> dict | None:
    """Ambil objek JSON-LD `JobPosting` dari HTML halaman detail Glints."""
    for m in re.finditer(r'application/ld\+json[^>]*>(.*?)</script>', html, re.S):
        raw = m.group(1).strip()
        # Kadang ada atribut data-next-head sebelum '>'.
        if raw.startswith('" data-next-head'):
            raw = raw.split(">", 1)[1]
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item.get("@type") == "JobPosting":
                    return item
        elif isinstance(data, dict) and data.get("@type") == "JobPosting":
            return data
    return None
