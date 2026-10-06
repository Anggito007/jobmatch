# JobMatch backend — Docker image (untuk Render free tier & VPS umum).
# fastembed (ONNX) + model multilingual ~118MB → image total <400MB, muat di
# Render free (512MB disk). Backend torch (requirements-torch.txt) opsional
# untuk VPS/Oracle bila ingin kualitas maksimal.

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

# CORS: izinkan semua origin (auth pakai Bearer token, bukan cookie).
ENV CORS_ORIGINS=*

EXPOSE 8000

# Render set env PORT; default 8000.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
