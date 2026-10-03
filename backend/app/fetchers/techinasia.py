"""Tech in Asia Jobs fetcher — Algolia search API (tanpa auth tambahan)."""
from __future__ import annotations

import httpx

from .base import BaseFetcher, Job

API_URL = "https://219wx3mpv4-dsn.algolia.net/1/indexes/*/queries"
ALGOLIA_APP_ID = "219WX3MPV4"
ALGOLIA_API_KEY = "b528008a75dc1c4402bfe0d8db8b3f8e"  # public search-only key

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    ),
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://www.techinasia.com",
    "Referer": "https://www.techinasia.com/",
    "x-algolia-agent": "Algolia for vanilla JavaScript 3.30.0;JS Helper 2.26.1",
    "x-algolia-application-id": ALGOLIA_APP_ID,
    "x-algolia-api-key": ALGOLIA_API_KEY,
}


class TechInAsiaFetcher(BaseFetcher):
    source_name = "techinasia"

    def fetch(
        self,
        keywords: list[str],
        location: str = "",
        page_size: int = 50,
        max_pages: int = 3,
    ) -> list[Job]:
        jobs: list[Job] = []
        term = " ".join(keywords)

        with httpx.Client(headers=HEADERS, timeout=30.0) as client:
            for page in range(max_pages):
                params = f"query={term}&hitsPerPage={page_size}&page={page}"
                body = {"requests": [{"indexName": "job_postings", "params": params}]}
                resp = client.post(API_URL, data=str(body).replace("'", '"'))
                resp.raise_for_status()
                results = resp.json().get("results") or []
                if not results:
                    break
                hits = results[0].get("hits") or []
                if not hits:
                    break
                jobs.extend(self._parse(h) for h in hits)
        return jobs

    @staticmethod
    def _parse(h: dict) -> Job:
        company = h.get("company") or {}
        city = h.get("city") or {}
        currency = h.get("currency") or {}
        slug = company.get("entity_slug") or ""
        job_id = h.get("objectID", "")
        url = h.get("url") or (
            f"https://www.techinasia.com/jobs/{job_id}"
            if job_id
            else f"https://www.techinasia.com/companies/{slug}"
        )
        salary = f"{currency.get('currency_symbol', '')}{h.get('salary_min', '')}-{h.get('salary_max', '')}".strip("-")
        return Job(
            source="techinasia",
            external_id=str(job_id),
            title=h.get("title", ""),
            company=company.get("name", ""),
            location=city.get("name", ""),
            description=(h.get("description") or "")[:500],
            job_type=", ".join(h.get("employment_types") or []),
            work_arrangement=h.get("remote", False) and "Remote" or "",
            url=url,
            posted_at=h.get("published_at", ""),
        )


if __name__ == "__main__":
    print(len(TechInAsiaFetcher().fetch(["backend"])))
