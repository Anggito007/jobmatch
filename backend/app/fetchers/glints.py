"""Glints fetcher — public GraphQL `searchJobsV3` + detail JSON-LD.

Search tidak menyertakan deskripsi (`descriptionJsonString` = null). Deskripsi
lengkap ada di halaman detail sebagai JSON-LD `JobPosting`. Maka setelah search,
kita fetch detail tiap job secara paralel untuk ambil description + skills.
"""
from __future__ import annotations

import json
import logging
import re
import time

import httpx

from .base import BaseFetcher, Job
from .utils import fetch_many, strip_html

log = logging.getLogger("jobmatch.fetchers.glints")

API_URL = "https://glints.com/api/v2-alc/graphql"
MAX_RETRIES = 3
RETRY_BACKOFF = 1.5  # detik, dikali percobaan ke-N

SEARCH_QUERY = """
query searchJobsV3($data: JobSearchConditionInput!) {
  searchJobsV3(data: $data) {
    jobsInPage {
      id
      title
      createdAt
      isRemote
      workArrangementOption
      type
      educationLevel
      minYearsOfExperience
      maxYearsOfExperience
      isActivelyHiring
      company { name }
      city { name }
      country { name }
      salaries { salaryType salaryMode minAmount maxAmount CurrencyCode }
      skills { mustHave skill { id name } }
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
    # WAJIB: tanpa Accept + Accept-Language, firewall Glints membalas 403
    # untuk operasi searchJobsV3 (koneksi dasar tetap 200 — makanya sulit
    # dideteksi). Ini penyebab pool Glints sempat tinggal 4 lowongan.
    "Accept": "*/*",
    "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
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
        page_size: int = 50,
        max_pages: int = 1,
        enrich: bool = False,
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
                payload = self._post_with_retry(client, body)
                if payload is None:
                    break
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

    @staticmethod
    def _post_with_retry(client: httpx.Client, body: dict) -> dict | None:
        """POST GraphQL; None bila halaman ini tidak bisa diambil.

        Penting: Glints hanya mengizinkan **halaman 1** tanpa login. Halaman
        berikutnya dibalas `403 {"message": "please login for more
        information"}`. Dulu exception-nya membatalkan SELURUH fetch — termasuk
        50 lowongan dari halaman 1 yang sudah berhasil diambil — sehingga pool
        Glints tinggal 4 lowongan basi. Sekarang kegagalan halaman lanjutan
        cukup menghentikan paginasi (return None), bukan menggagalkan semuanya.
        """
        last_status = None
        for attempt in range(MAX_RETRIES):
            try:
                resp = client.post(API_URL, json=body)
            except httpx.HTTPError:
                time.sleep(RETRY_BACKOFF * (attempt + 1))
                continue
            if resp.status_code == 200:
                try:
                    return resp.json()
                except ValueError:
                    return None
            last_status = resp.status_code
            # 403 "please login" = batas keras, tidak ada gunanya retry.
            if resp.status_code == 403 and "please login" in resp.text.lower():
                return None
            if resp.status_code in (403, 429) or resp.status_code >= 500:
                time.sleep(RETRY_BACKOFF * (attempt + 1))
                continue
            return None
        log.warning("Glints: halaman dilewati setelah %s percobaan (HTTP %s)", MAX_RETRIES, last_status)
        return None

    def _enrich_details(self, jobs: list[Job], max_workers: int = 3, max_enrich: int = 25) -> None:
        """Fetch halaman detail tiap job → ambil description + skills dari JSON-LD.

        Dibatasi ketat: mengirim puluhan permintaan HTML beruntun memicu
        firewall Glints, dan ban-nya ikut memblokir operasi pencarian
        berikutnya (inilah yang dulu membuat pool Glints tinggal 4 lowongan).
        Sebagian besar data sudah didapat dari search, jadi pengayaan hanya
        pelengkap dan tidak wajib berhasil.
        """
        url_map = {j.url: j for j in jobs if j.url}
        urls = list(url_map.keys())[:max_enrich]
        try:
            pages = fetch_many(urls, _HTML_HEADERS, max_workers=max_workers)
        except Exception:  # noqa: BLE001 — pengayaan gagal bukan masalah fatal
            return
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

        # Data terstruktur dari skema Glints — jauh lebih akurat daripada
        # menebak dari teks (dulu `work_arrangement` kosong untuk 90% lowongan).
        is_remote = item.get("isRemote")
        arrangement = item.get("workArrangementOption") or ""
        if not arrangement and is_remote:
            arrangement = "Remote"

        # skills: list of {mustHave: bool, skill: {id, name, translationKey}}
        skills: list[str] = []
        for s in item.get("skills") or []:
            if not isinstance(s, dict):
                continue
            detail = s.get("skill")
            if isinstance(detail, dict) and detail.get("name"):
                skills.append(str(detail["name"]))

        # Susun konteks tambahan agar matching punya bahan (deskripsi lengkap
        # tetap diambil dari halaman detail bila memungkinkan).
        extra: list[str] = []
        if item.get("educationLevel"):
            extra.append(f"Education: {item['educationLevel']}")
        if item.get("minYearsOfExperience") is not None:
            extra.append(
                f"Experience: {item.get('minYearsOfExperience')}-"
                f"{item.get('maxYearsOfExperience')} years"
            )
        if item.get("isActivelyHiring"):
            extra.append("Actively hiring")
        if skills:
            extra.append("Skills: " + ", ".join(skills))

        return Job(
            source="glints",
            external_id=job_id,
            title=item.get("title", ""),
            company=(item.get("company") or {}).get("name", ""),
            location=city or country or "",
            salary_min=salary.get("minAmount"),
            salary_max=salary.get("maxAmount"),
            currency=salary.get("CurrencyCode", "IDR"),
            job_type=str(item.get("type") or ""),
            work_arrangement=arrangement,
            requirements=" | ".join(extra),
            skills=skills,
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
