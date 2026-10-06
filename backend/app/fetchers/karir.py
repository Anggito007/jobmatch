"""Karir.com fetcher — public gateway API + detail via _next/data.

Search hanya memberi metadata; deskripsi lengkap ada di halaman detail Next.js:
`/_next/data/<buildId>/opportunities/<id>.json` (buildId berubah tiap deploy,
diambil dari halaman utama). responseData berisi requirements, responsibilities,
required_skills, location, dsb.
"""
from __future__ import annotations

import json
import re

import httpx

from .base import BaseFetcher, Job
from .utils import fetch_many, strip_html

API_URL = "https://gateway2-beta.karir.com/v2/search/opportunities"
HOME_URL = "https://karir.com/"

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

_HTML_HEADERS = {
    "User-Agent": HEADERS["User-Agent"],
    "Accept": "text/html,application/xhtml+xml",
}

_BUILD_ID_RE = re.compile(r'"buildId":"([^"]+)"')


class KarirFetcher(BaseFetcher):
    source_name = "karir"

    def fetch(
        self,
        keywords: list[str],
        location: str = "",
        page_size: int = 10,
        max_pages: int = 15,
        enrich: bool = True,
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

        if enrich and jobs:
            self._enrich_details(jobs)
        return jobs

    def _enrich_details(self, jobs: list[Job], max_workers: int = 6) -> None:
        """Fetch detail tiap job via _next/data (perlu buildId terbaru)."""
        build_id = self._get_build_id()
        if not build_id:
            return
        url_map = {}
        for j in jobs:
            url = (
                f"https://karir.com/_next/data/{build_id}/opportunities/{j.external_id}.json"
                f"?index={j.external_id}"
            )
            url_map[url] = j
        pages = fetch_many(list(url_map.keys()), _HTML_HEADERS, max_workers=max_workers)
        for url, text in pages.items():
            if not text:
                continue
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                continue
            rd = (data.get("pageProps") or {}).get("responseData")
            if rd:
                self._apply_detail(url_map[url], rd)

    @staticmethod
    def _apply_detail(job: Job, rd: dict) -> None:
        desc_parts = [
            strip_html(rd.get("responsibilities")),
            strip_html(rd.get("requirements")),
        ]
        job.description = " ".join(p for p in desc_parts if p) or job.description
        if rd.get("location"):
            job.location = rd["location"]
        if rd.get("job_type"):
            job.job_type = rd["job_type"]
        skills = rd.get("required_skills")
        if isinstance(skills, list) and skills:
            job.skills = [s for s in skills if isinstance(s, str)] or job.skills
        if rd.get("salary_lower") is not None:
            job.salary_min = rd["salary_lower"]
        if rd.get("salary_upper") is not None:
            job.salary_max = rd["salary_upper"]

    def _get_build_id(self) -> str | None:
        """Ambil buildId Next.js dari halaman utama (berubah tiap deploy)."""
        try:
            with httpx.Client(headers=_HTML_HEADERS, timeout=20.0, follow_redirects=True) as c:
                r = c.get(HOME_URL)
                m = _BUILD_ID_RE.search(r.text)
                return m.group(1) if m else None
        except Exception:
            return None

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
