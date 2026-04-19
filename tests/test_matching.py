"""Tests for matching logic using a stub embedding model (no real model download)."""
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch


def _stub_encode(texts: list[str]) -> list[np.ndarray]:
    """Deterministic stub: hash text to a 384-dim float vector."""
    results = []
    for text in texts:
        seed = sum(ord(c) for c in text) % (2**31)
        rng = np.random.default_rng(seed)
        vec = rng.standard_normal(384).astype(np.float32)
        vec /= np.linalg.norm(vec)
        results.append(vec)
    return results


def _stub_encode_one(text: str) -> np.ndarray:
    return _stub_encode([text])[0]


@pytest.fixture()
def patched_embeddings(cv_file: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch embedding functions and redirect CV_FILE to test fixture."""
    import career_ops_mcp.embeddings as emb_mod
    import career_ops_mcp.matching as matching_mod
    import career_ops_mcp.config as config_mod

    monkeypatch.setattr(emb_mod, "encode", _stub_encode)
    monkeypatch.setattr(emb_mod, "encode_one", _stub_encode_one)
    monkeypatch.setattr(config_mod, "CV_FILE", cv_file)


def test_match_returns_expected_keys(patched_embeddings: None, cv_file: Path) -> None:
    from career_ops_mcp.matching import match_cv_to_jd
    result = match_cv_to_jd("We are looking for a forward deployed engineer with Python skills.")
    assert "overall" in result
    assert "per_section" in result
    assert "top_bullets" in result
    assert "gap_hints" in result


def test_per_section_has_all_sections(patched_embeddings: None, cv_file: Path) -> None:
    from career_ops_mcp.matching import match_cv_to_jd
    result = match_cv_to_jd("Python backend engineer role.")
    slugs = {s["slug"] for s in result["per_section"]}
    assert "professional-experience" in slugs
    assert "technical-skills" in slugs


def test_overall_in_range(patched_embeddings: None, cv_file: Path) -> None:
    from career_ops_mcp.matching import match_cv_to_jd
    result = match_cv_to_jd("Solutions architect with cloud and API experience.")
    assert 0.0 <= result["overall"] <= 1.0


def test_top_bullets_count(patched_embeddings: None, cv_file: Path) -> None:
    from career_ops_mcp.matching import match_cv_to_jd
    result = match_cv_to_jd("Engineer with Python experience.")
    assert len(result["top_bullets"]) <= 5
    if result["top_bullets"]:
        assert "bullet" in result["top_bullets"][0]
        assert "score" in result["top_bullets"][0]
