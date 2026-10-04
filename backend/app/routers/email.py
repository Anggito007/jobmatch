"""Email digest: kirim ringkasan lowongan cocok ke email user.

Wajib login. Menggunakan CV terbaru yang tersimpan di akun user.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user
from app.config import settings
from app.email import build_digest_html, send_email
from app.matching.embedder import get_embedder
from app.models import User
from app.routers.match import score_rows
from app.store import get_jobs, get_latest_cv

router = APIRouter()


@router.post("")
def digest(user: User = Depends(get_current_user), top_n: int = 10) -> dict:
    cv = get_latest_cv(user.id)
    if cv is None or not cv.embedding:
        raise HTTPException(
            status_code=400,
            detail="Belum ada CV tersimpan. Upload CV dulu lewat /api/match (dalam keadaan login).",
        )

    rows = get_jobs(limit=5000)
    if not rows:
        raise HTTPException(status_code=400, detail="Pool lowongan kosong. Jalankan /api/jobs/refresh dulu.")

    embedder = get_embedder()
    # Rekonstruksi profil sederhana untuk scoring (pakai data CV tersimpan).
    from app.cv.profile import CVProfile

    profile = CVProfile(
        raw_text=cv.raw_text,
        skills=cv.skills or [],
        years_experience=cv.years_experience,
        education=cv.education,
        target_role=cv.target_role,
    )
    results = score_rows(rows, profile, embedder, list(cv.embedding))

    html = build_digest_html(results, top_n=top_n)

    recipients = [e.strip() for e in settings.digest_recipients.split(",") if e.strip()]
    if not recipients:
        recipients = [user.email]

    sent = send_email(recipients, "JobMatch — Lowongan Cocok Hari Ini", html)

    return {
        "sent": sent,
        "to": recipients,
        "top_matches": results[:top_n],
        "note": "SMTP belum dikonfigurasi (isi SMTP_USER/SMTP_PASSWORD) — ini hanya preview."
        if not sent
        else "Digest terkirim.",
    }
