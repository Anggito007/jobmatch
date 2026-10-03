"""Embedder — wrapper lazy-loading untuk sentence-transformers.

Model dimuat SEKALI (singleton) karena loading ~470MB model itu lambat;
selebihnya hanya encoding in-memory yang cepat. Jangan buat instance baru
per-request — pakai `get_embedder()`.
"""
from __future__ import annotations

import threading
from typing import Sequence

# Model multibahasa (50+ bahasa termasuk Indonesia) — 384 dims, ~470MB.
# Pilihan yang seimbang antara akurasi dan footprint.
DEFAULT_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"


class Embedder:
    """Thread-safe lazy singleton di sekitar SentenceTransformer."""

    _instance: "Embedder | None" = None
    _lock = threading.Lock()

    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        self.model_name = model_name
        self._model = None

    @classmethod
    def get(cls, model_name: str = DEFAULT_MODEL) -> "Embedder":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(model_name)
            return cls._instance

    @property
    def model(self):
        if self._model is None:
            # Impor di dalam agar modul matching tetap bisa diimpor
            # tanpa sentence-transformers terinstal (untuk CI/tanpa ML).
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        """Encode satu/beberapa teks menjadi vektor float."""
        if not texts:
            return []
        embeddings = self.model.encode(
            list(texts), normalize_embeddings=True, convert_to_numpy=True
        )
        return [e.tolist() for e in embeddings]

    def embed_one(self, text: str) -> list[float]:
        return self.encode([text])[0]


def get_embedder() -> Embedder:
    return Embedder.get()
