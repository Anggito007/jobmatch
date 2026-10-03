# JobMatch backend — Docker image.
# Catatan: model sentence-transformers (~470MB) diunduh saat build image,
# supaya runtime tidak lambat. Di Render free tier (512MB disk) ini TIDAK muat —
# lihat DEPLOYMENT.md untuk opsi.

FROM python:3.12-slim

WORKDIR /app

# System deps minimal (pdfplumber butuh ini di beberapa kasus).
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts

# Pre-download model embedding ke dalam image (bukan saat runtime).
RUN python -m scripts.warmup_model

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
