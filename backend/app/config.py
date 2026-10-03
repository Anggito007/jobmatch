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


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
