# JobMatch backend — Docker image (kompatibel dengan Hugging Face Spaces).
# HF Spaces Docker SDK: server harus listen di $PORT (default 7860),
# persistent storage di /data.
#
# Model sentence-transformers (~470MB) diunduh saat BUILD image, supaya
# runtime tidak lambat.

FROM python:3.12-slim

WORKDIR /app

# System deps minimal.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts

# Pre-download model embedding ke dalam image (bukan saat runtime).
RUN python -m scripts.warmup_model

# DB persistent di /data (HF Spaces menyediakan volume ini secara otomatis).
ENV DATABASE_URL=sqlite:////data/jobmatch.db
ENV CORS_ORIGINS=*

EXPOSE 7860

# Listen di $PORT (HF Spaces set PORT=7860; fallback 7860).
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
