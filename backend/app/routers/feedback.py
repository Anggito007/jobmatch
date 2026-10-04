"""Feedback relevansi lowongan (👍/👎) — wajib login."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import get_current_user
from app.models import User
from app.store import save_feedback

router = APIRouter()


class FeedbackIn(BaseModel):
    job_id: str       # format "source:external_id"
    is_relevant: bool


@router.post("")
def feedback(data: FeedbackIn, user: User = Depends(get_current_user)) -> dict:
    source, sep, ext_id = data.job_id.partition(":")
    if not sep or not ext_id:
        raise HTTPException(status_code=400, detail="job_id harus format 'source:external_id'")
    action = save_feedback(user.id, source, ext_id, data.is_relevant)
    return {"action": action, "job_id": data.job_id, "is_relevant": data.is_relevant}
