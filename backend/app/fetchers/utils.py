"""Util umum untuk fetcher: strip HTML, fetch detail paralel."""
from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx

_TAG_RE = re.compile(r"<[^>]+>")


def strip_html(html: str | None) -> str:
    """Ubah HTML → teks polos (hapus tag, rapikan whitespace)."""
    if not html:
        return ""
    text = _TAG_RE.sub(" ", html)
    # HTML entities umum.
    text = (
        text.replace("&amp;", "&")
        .replace("&nbsp;", " ")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&#39;", "'")
        .replace("&quot;", '"')
    )
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def fetch_many(urls: list[str], headers: dict, max_workers: int = 6, timeout: float = 25.0) -> dict[str, str | None]:
    """Fetch banyak URL secara paralel. Return dict url → text (None bila gagal).

    Dipakai untuk memperkaya deskripsi job dari halaman detail. Gagal per-URL
    tidak menggagalkan seluruh batch.
    """
    results: dict[str, str | None] = {}

    def _one(url: str) -> tuple[str, str | None]:
        try:
            with httpx.Client(headers=headers, timeout=timeout, follow_redirects=True) as c:
                r = c.get(url)
                return url, r.text if r.status_code == 200 else None
        except Exception:
            return url, None

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_one, u): u for u in urls}
        for fut in as_completed(futures):
            url, text = fut.result()
            results[url] = text

    return results
