"""Preferensi / filter pencarian — simpan & ambil (persisten per user)."""
from __future__ import annotations

from fastapi import APIRouter, Body, Depends

from app.auth import get_optional_user
from app.models import User
from app.preferences import from_dict, to_dict
from app.store import get_preferences, save_preferences

router = APIRouter()


@router.get("")
def get(user: User | None = Depends(get_optional_user)) -> dict:
    """Ambil preferensi tersimpan user (kosong bila belum pernah disimpan)."""
    prefs = get_preferences(user.id if user else None)
    if prefs is None:
        return {"preferences": to_dict(from_dict(None))}
    return {"preferences": to_dict(from_dict(_row_to_dict(prefs)))}


@router.post("")
def save(data: dict = Body(...), user: User | None = Depends(get_optional_user)) -> dict:
    """Simpan preferensi user (upsert)."""
    f = from_dict(data)
    save_preferences(user.id if user else None, to_dict(f))
    return {"preferences": to_dict(f), "saved": True}


def _row_to_dict(prefs) -> dict:
    """Konversi model ORM → dict (hanya kolom preferensi)."""
    keys = [
        "locations", "position_levels", "job_types", "specializations",
        "education_levels", "preferred_companies", "excluded_companies",
        "min_salary", "max_salary", "salary_currency", "salary_not_specified",
        "remote", "hybrid", "work_abroad", "fresh_graduate", "quick_response",
        "sort_by",
    ]
    return {k: getattr(prefs, k) for k in keys}
