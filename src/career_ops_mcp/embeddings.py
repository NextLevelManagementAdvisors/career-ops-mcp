from __future__ import annotations

import numpy as np
from fastembed import TextEmbedding

from career_ops_mcp.config import CACHE_DIR, EMBED_MODEL

_model: TextEmbedding | None = None


def get_model() -> TextEmbedding:
    global _model
    if _model is None:
        # Pin the model cache next to the index; fastembed's default is the
        # OS temp dir, which macOS purges, leaving a half-deleted snapshot.
        _model = TextEmbedding(EMBED_MODEL, cache_dir=str(CACHE_DIR / "models"))
    return _model


def encode(texts: list[str]) -> list[np.ndarray]:
    if not texts:
        return []
    return list(get_model().embed(texts))


def encode_one(text: str) -> np.ndarray:
    return encode([text])[0]
