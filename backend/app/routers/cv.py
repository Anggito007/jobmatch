"""CV-related endpoints."""
from fastapi import APIRouter, File, UploadFile

from app.cv.extract import extract_text

router = APIRouter()


@router.post("/upload")
async def upload_cv(file: UploadFile = File(...)) -> dict:
    """Terima CV (PDF/DOCX), ekstrak teks mentahnya."""
    content = await file.read()
    text = extract_text(content, file.filename or "")
    return {
        "filename": file.filename,
        "char_count": len(text),
        "preview": text[:500],
    }
