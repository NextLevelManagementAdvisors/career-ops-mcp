from __future__ import annotations

import numpy as np

from career_ops_mcp import embeddings as emb_mod
from career_ops_mcp import storage
from career_ops_mcp.config import CV_FILE
from career_ops_mcp.parsers import cv as cv_parser
from career_ops_mcp.text import chunk_text


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def match_cv_to_jd(jd_text: str) -> dict:
    """Score CV sections against JD text and return structured match result."""
    if not CV_FILE.exists():
        return {"error": f"cv.md not found at {CV_FILE}"}

    cv = cv_parser.parse(CV_FILE)
    jd_vec = emb_mod.encode_one(jd_text)

    # Per-section scores
    per_section = []
    section_vecs: dict[str, np.ndarray] = {}
    for section in cv.sections:
        if not section.body.strip():
            continue
        sec_vec = emb_mod.encode_one(section.body)
        section_vecs[section.slug] = sec_vec
        score = max(0.0, _cosine(jd_vec, sec_vec))
        per_section.append({
            "section": section.heading,
            "slug": section.slug,
            "score": round(score, 4),
        })

    per_section.sort(key=lambda x: x["score"], reverse=True)

    # Top matching bullets from professional experience
    exp_section = cv.section("professional-experience")
    top_bullets: list[dict] = []
    if exp_section and exp_section.bullets:
        bullet_vecs = emb_mod.encode(exp_section.bullets)
        scored_bullets = [
            {"bullet": b, "score": round(_cosine(jd_vec, v), 4)}
            for b, v in zip(exp_section.bullets, bullet_vecs)
        ]
        scored_bullets.sort(key=lambda x: x["score"], reverse=True)
        top_bullets = scored_bullets[:5]

    # Overall score: weighted average of section scores
    if per_section:
        overall = round(sum(s["score"] for s in per_section) / len(per_section), 4)
    else:
        overall = 0.0

    # Gap hints: bottom third of sections
    gap_threshold = len(per_section) // 3
    gap_hints = [s["section"] for s in per_section[len(per_section) - gap_threshold:]] if gap_threshold else []

    return {
        "overall": overall,
        "per_section": per_section,
        "top_bullets": top_bullets,
        "gap_hints": gap_hints,
    }
