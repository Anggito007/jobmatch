"""Glints fetcher — public GraphQL `searchJobsV3` di /api/v2-alc/graphql.

Schema undocumented (reverse-engineered dari halaman search Glints). Endpoint
lama `/api/graphql` diganti `/api/v2-alc/graphql`; operasi lama `opportunities`
diganti `searchJobsV3`.
"""
from __future__ import annotations

import httpx

from .base import BaseFetcher, Job

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


class GlintsFetcher(BaseFetcher):
    source_name = "glints"

    def fetch(
        self,
        keywords: list[str],
        location: str = "",
        country: str = "ID",
        page_size: int = 30,
        max_pages: int = 3,
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
        return jobs

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
