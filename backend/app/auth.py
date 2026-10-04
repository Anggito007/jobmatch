"""Auth: hash password (pbkdf2), token sesi opaque, dependency current user.

Tanpa dependensi eksternal (pakai hashlib + secrets dari stdlib). Token disimpan
di tabel auth_sessions; frontend kirim via header `Authorization: Bearer <token>`.
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select

from app.config import settings
from app.db import SessionLocal
from app.models import AuthSession, User

_ITERATIONS = 200_000


def _utcnow_naive() -> datetime:
    """Naive UTC 'now' — SQLite menyimpan datetime tanpa tzinfo."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
    return f"{salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, hash_hex = stored.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
        return secrets.compare_digest(dk.hex(), hash_hex)
    except Exception:
        return False


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    with SessionLocal() as db:
        db.add(
            AuthSession(
                token=token,
                user_id=user_id,
                expires_at=_utcnow_naive() + timedelta(days=settings.session_ttl_days),
            )
        )
        db.commit()
    return token


def get_optional_user(authorization: str = Header(default="")) -> User | None:
    """Dependency: ambil user bila token valid; None bila anonim/token invalid."""
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        return None
    with SessionLocal() as db:
        sess = db.scalar(select(AuthSession).where(AuthSession.token == token))
        if not sess or sess.expires_at < _utcnow_naive():
            return None
        return db.get(User, sess.user_id)


def get_current_user(authorization: str = Header(default="")) -> User:
    """Dependency: ambil user dari token Bearer (wajib login)."""
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Belum login")
    with SessionLocal() as db:
        sess = db.scalar(select(AuthSession).where(AuthSession.token == token))
        if not sess or sess.expires_at < _utcnow_naive():
            raise HTTPException(status_code=401, detail="Sesi tidak valid / kedaluwarsa")
        user = db.get(User, sess.user_id)
        if not user:
            raise HTTPException(status_code=401, detail="Pengguna tidak ditemukan")
        return user
