from __future__ import annotations

import numpy as np
from fastembed import TextEmbedding

from career_ops_mcp.config import EMBED_MODEL

_model: TextEmbedding | None = None


def get_model() -> TextEmbedding:
    global _model
    if _model is None:
        _model = TextEmbedding(EMBED_MODEL)
    return _model


def encode(texts: list[str]) -> list[np.ndarray]:
    if not texts:
        return []
    return list(get_model().embed(texts))


def encode_one(text: str) -> np.ndarray:
    return encode([text])[0]
