"""Embedder — wrapper lazy-loading, dua backend otomatis.

Backend dipilih otomatis saat `get_embedder()` pertama dipanggil:
1. `fastembed` (ONNX, ringan ~200MB total) — dipakai di hosting free-tier (Render).
2. `sentence-transformers` (torch, ~1GB) — fallback bila fastembed tidak ada,
   atau di VPS/Oracle untuk kualitas maksimal.

Kedua backend memakai MODEL YANG SAMA (`paraphrase-multilingual-MiniLM-L12-v2`,
384 dims), sehingga vektor yang dihasilkan setara dan skor konsisten. Model
dimuat SEKALI (singleton) karena loading lambat; pakai `get_embedder()`.
"""
from __future__ import annotations

import threading
from typing import Sequence

# Model multibahasa (50+ bahasa termasuk Indonesia) — 384 dims.
DEFAULT_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"


class Embedder:
    """Thread-safe lazy singleton. Backend auto-detected."""

    _instance: "Embedder | None" = None
    _lock = threading.Lock()

    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        self.model_name = model_name
        self._model = None
        self._backend = None

    @classmethod
    def get(cls, model_name: str = DEFAULT_MODEL) -> "Embedder":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(model_name)
            return cls._instance

    def _load(self):
        """Muat model via backend pertama yang tersedia."""
        # 1. fastembed (ringan, tanpa torch) — prioritas untuk free tier.
        try:
            from fastembed import TextEmbedding

            full = f"sentence-transformers/{self.model_name}"
            self._model = TextEmbedding(full)
            self._backend = "fastembed"
            return
        except Exception:
            pass

        # 2. sentence-transformers (torch) — fallback kualitas penuh.
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
            self._backend = "torch"
            return
        except Exception as e:
            raise RuntimeError(
                "Tidak ada backend embedding tersedia. Install fastembed ATAU "
                f"sentence-transformers. Detail: {e}"
            ) from e

    @property
    def backend(self) -> str | None:
        if self._model is None:
            self._load()
        return self._backend

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        """Encode satu/beberapa teks menjadi vektor float (TERNORMALISASI unit)."""
        if not texts:
            return []
        if self._model is None:
            self._load()

        if self._backend == "fastembed":
            # fastembed TIDAK menormalisasi output — harus dinormalisasi manual
            # supaya cosine_similarity (dot product) valid.
            import numpy as np

            vecs = [np.asarray(v, dtype="float32") for v in self._model.embed(list(texts))]
            out: list[list[float]] = []
            for v in vecs:
                n = float(np.linalg.norm(v))
                v = v / n if n > 0 else v
                out.append(v.tolist())
            return out

        # torch / sentence-transformers (normalize_embeddings=True sudah unit).
        import numpy as np

        arr = self._model.encode(
            list(texts), normalize_embeddings=True, convert_to_numpy=True
        )
        if isinstance(arr, np.ndarray):
            return arr.tolist()
        return [a.tolist() for a in arr]

    def embed_one(self, text: str) -> list[float]:
        return self.encode([text])[0]


def get_embedder() -> Embedder:
    return Embedder.get()
