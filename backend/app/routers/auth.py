"""Auth endpoints: register, login, me."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import create_session, get_current_user, hash_password, verify_password
from app.models import User
from app.store import create_user, get_user_by_email

router = APIRouter()


class RegisterIn(BaseModel):
    email: str
    password: str


class LoginIn(BaseModel):
    email: str
    password: str


def _normalize(email: str) -> str:
    return email.strip().lower()


@router.post("/register")
def register(data: RegisterIn) -> dict:
    email = _normalize(data.email)
    if not email or "@" not in email or "." not in email:
        raise HTTPException(status_code=400, detail="Email tidak valid")
    if len(data.password) < 6:
        raise HTTPException(status_code=400, detail="Password minimal 6 karakter")

    user = create_user(email, hash_password(data.password))
    if user is None:
        raise HTTPException(status_code=409, detail="Email sudah terdaftar")
    token = create_session(user.id)
    return {"token": token, "email": user.email}


@router.post("/login")
def login(data: LoginIn) -> dict:
    email = _normalize(data.email)
    user = get_user_by_email(email)
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email atau password salah")
    token = create_session(user.id)
    return {"token": token, "email": user.email}


@router.get("/me")
def me(user: User = Depends(get_current_user)) -> dict:
    return {"id": user.id, "email": user.email}
