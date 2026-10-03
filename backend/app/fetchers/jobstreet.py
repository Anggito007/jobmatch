"""JobStreet (SEEK) fetcher — v5 JobSearch REST API.

Endpoint publik tanpa auth yang dipakai frontend id.jobstreet.com sendiri.
REST v4 lama (`chalice-search`) sudah deprecated (404); v5 ini penggantinya.
"""
from __future__ import annotations

import httpx

from .base import BaseFetcher, Job

SEARCH_URL = "https://id.jobstreet.com/api/jobsearch/v5/search"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Referer": "https://id.jobstreet.com/id/jobs",
}


class JobStreetFetcher(BaseFetcher):
    source_name = "jobstreet"

    def fetch(
        self,
        keywords: list[str],
        location: str = "",
        page_size: int = 20,
        max_pages: int = 1,
    ) -> list[Job]:
        jobs: list[Job] = []
        query = " ".join(keywords)

        with httpx.Client(headers=HEADERS, timeout=30.0) as client:
            for page in range(1, max_pages + 1):
                params = {
                    "siteKey": "ID-Main",
                    "keywords": query,
                    "where": location,
                    "pageSize": page_size,
                    "page": page,
                }
                resp = client.get(SEARCH_URL, params=params)
                resp.raise_for_status()
                items = resp.json().get("data", [])
                if not items:
                    break
                jobs.extend(self._parse(item) for item in items)
        return jobs

    @staticmethod
    def _parse(item: dict) -> Job:
        advertiser = item.get("advertiser") or {}
        locations = item.get("locations") or [{}]
        arrangements = item.get("workArrangements") or {}
        return Job(
            source="jobstreet",
            external_id=str(item.get("id", "")),
            title=item.get("title", ""),
            company=advertiser.get("description", ""),
            location=locations[0].get("label", ""),
            description=item.get("teaser", ""),
            requirements="\n".join(item.get("bulletPoints") or []),
            skills=list(item.get("bulletPoints") or []),
            job_type=", ".join(item.get("workTypes") or []),
            work_arrangement=arrangements.get("displayText", ""),
            url=f"https://id.jobstreet.com/id/job/{item.get('id', '')}",
            posted_at=item.get("listingDate", ""),
        )
