"""Application settings, loaded from environment / .env."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "JobMatch"
    database_url: str = "sqlite:///./jobmatch.db"

    # CORS origins untuk frontend. Tambahkan URL Vercel saat sudah deploy.
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Kunci preferensi lowongan default (bisa di-override per user nanti).
    default_keywords: list[str] = ["software engineer", "backend", "programmer"]

    # Interval fetch scheduler (jam).
    fetch_interval_hours: int = 6

    # Auth — lama sesi login (hari).
    session_ttl_days: int = 30

    # Email digest (Gmail SMTP). Kosongkan smtp_user/smtp_password untuk
    # menonaktifkan pengiriman (digest tetap bisa dibangun, tidak dikirim).
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""       # email Gmail pengirim
    smtp_password: str = ""   # App Password Gmail (bukan password biasa)
    digest_from: str = ""     # default = smtp_user
    digest_recipients: str = ""  # pisahkan koma bila banyak


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
