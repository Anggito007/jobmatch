"""Email digest: bangun & kirim ringkasan lowongan cocok via SMTP (Gmail).

Tanpa kredensial SMTP (settings.smtp_user/smtp_password kosong), digest tetap
dibangun dan dikembalikan sebagai preview, tapi tidak dikirim.
"""
from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings


def build_digest_html(matches: list[dict], top_n: int = 10) -> str:
    """Bangun body HTML digest dari daftar match (sudah terurut)."""
    items = matches[:top_n]
    rows = []
    for m in items:
        score = f"{m['score'] * 100:.0f}%"
        salary = ""
        if m.get("salary_max"):
            salary = f" — Rp{m['salary_max']:,.0f}".replace(",", ".")
        rows.append(
            f"<li style='margin-bottom:12px'>"
            f"<a href='{m['url']}' style='color:#4f8cff'>{m['title']}</a><br/>"
            f"<span style='color:#93a3b8;font-size:13px'>{m['company']} · {m['location']}{salary}</span><br/>"
            f"<span style='color:#34d399;font-size:12px'>Kecocokan {score}</span>"
            f"</li>"
        )
    body = (
        "<div style='background:#0b0f17;color:#e6edf7;padding:24px;font-family:Arial'>"
        "<h2 style='margin-top:0'>JobMatch — Lowongan Cocok Hari Ini</h2>"
        f"<p style='color:#93a3b8'>Berikut {len(items)} lowongan paling cocok dengan CV kamu:</p>"
        f"<ul style='list-style:none;padding:0'>{''.join(rows)}</ul>"
        "<p style='color:#93a3b8;font-size:12px'>Dikirim otomatis oleh JobMatch.</p>"
        "</div>"
    )
    return body


def send_email(to_emails: list[str], subject: str, html: str) -> bool:
    """Kirim email via SMTP. Return False bila SMTP tidak dikonfigurasi."""
    if not settings.smtp_user or not settings.smtp_password or not to_emails:
        return False
    from_addr = settings.digest_from or settings.smtp_user

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_emails)
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(from_addr, to_emails, msg.as_string())
    return True
