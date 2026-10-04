"""Simpan lowongan + status lamaran — wajib login."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.auth import get_current_user
from app.models import User
from app.store import delete_saved, list_saved, save_job

router = APIRouter()


class SaveIn(BaseModel):
    job_id: str           # format "source:external_id"
    status: str = "saved"  # saved | applied


def _split(job_id: str) -> tuple[str, str]:
    source, sep, ext_id = job_id.partition(":")
    if not sep or not ext_id:
        raise HTTPException(status_code=400, detail="job_id harus format 'source:external_id'")
    return source, ext_id


@router.get("")
def my_saved(user: User = Depends(get_current_user)) -> dict:
    return {"saved": list_saved(user.id)}


@router.post("")
def add(data: SaveIn, user: User = Depends(get_current_user)) -> dict:
    if data.status not in ("saved", "applied"):
        raise HTTPException(status_code=400, detail="status harus 'saved' atau 'applied'")
    source, ext_id = _split(data.job_id)
    action = save_job(user.id, source, ext_id, data.status)
    return {"action": action, "job_id": data.job_id, "status": data.status}


@router.delete("")
def remove(job_id: str = Query(...), user: User = Depends(get_current_user)) -> dict:
    source, ext_id = _split(job_id)
    ok = delete_saved(user.id, source, ext_id)
    return {"deleted": ok, "job_id": job_id}
