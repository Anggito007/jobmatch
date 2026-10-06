"""Pre-download & load model embedding (sekali), supaya request pertama cepat.

Run:
    python -m scripts.warmup_model
"""
from app.matching.embedder import get_embedder


def main() -> None:
    print("Memuat model embedding (unduh model ONNX ~118MB jika belum ada cache)...")
    emb = get_embedder()
    vec = emb.embed_one("Backend engineer Python FastAPI IoT")
    print(f"Model siap (backend: {emb.backend}). Dimensi vektor: {len(vec)}")
    print(f"Contoh 5 nilai pertama: {vec[:5]}")


if __name__ == "__main__":
    main()
