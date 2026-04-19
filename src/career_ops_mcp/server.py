from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from career_ops_mcp.config import CV_FILE, REPORTS_DIR
from career_ops_mcp.parsers import cv as cv_parser
from career_ops_mcp.parsers import reports as rep_parser
from career_ops_mcp import tools

mcp = FastMCP(
    "career-ops",
    instructions=(
        "Read-only access to Eric's job search data from career-ops. "
        "Data source: ~/Projects/career-ops. Tools for querying applications, "
        "semantic search, CV↔JD matching, pipeline, portals, and states."
    ),
)


# ── Tools ────────────────────────────────────────────────────────────────────

@mcp.tool()
def list_applications(
    status: str | None = None,
    company: str | None = None,
    since: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """List tracked job applications. Filter by status, company substring, or ISO date (since)."""
    return tools.list_applications(status=status, company=company, since=since, limit=limit)


@mcp.tool()
def get_application(company: str, role: str | None = None) -> dict | list[dict]:
    """Get detail for a specific application by company name. Returns the evaluation report if available."""
    return tools.get_application(company=company, role=role)


@mcp.tool()
def search_applications_semantic(query: str, top_k: int = 5) -> list[dict]:
    """Semantic search over applications, reports, and CV sections using local embeddings."""
    return tools.search_applications_semantic(query=query, top_k=top_k)


@mcp.tool()
def match_cv_to_jd(
    jd_text: str | None = None,
    jd_url: str | None = None,
    report_id: str | None = None,
) -> dict:
    """Score Eric's CV against a JD. Returns per-section scores, top matching bullets, and gap hints.
    Provide one of: jd_text (pasted), jd_url (fetched), or report_id (e.g. '012')."""
    return tools.match_cv_to_jd(jd_text=jd_text, jd_url=jd_url, report_id=report_id)


@mcp.tool()
def list_portals(enabled_only: bool = True, company: str | None = None) -> list[dict]:
    """List companies configured in the career-ops portal scanner."""
    return tools.list_portals(enabled_only=enabled_only, company=company)


@mcp.tool()
def list_pipeline(bucket: str = "pending", limit: int = 100) -> list[dict]:
    """List entries in the evaluation pipeline. Buckets: pending, processed, pendientes."""
    return tools.list_pipeline(bucket=bucket, limit=limit)


@mcp.tool()
def list_states() -> list[dict]:
    """List canonical application statuses and their aliases."""
    return tools.list_states()


# ── Resources ────────────────────────────────────────────────────────────────

@mcp.resource("career-ops://cv")
def get_cv() -> str:
    """Eric's full canonical CV/resume (cv.md)."""
    if not CV_FILE.exists():
        return f"cv.md not found at {CV_FILE}"
    return CV_FILE.read_text(encoding="utf-8")


@mcp.resource("career-ops://cv/{section}")
def get_cv_section(section: str) -> str:
    """A specific section of Eric's CV by slug (e.g. professional-experience, technical-skills)."""
    if not CV_FILE.exists():
        return f"cv.md not found at {CV_FILE}"
    cv = cv_parser.parse(CV_FILE)
    sec = cv.section(section)
    if sec is None:
        available = ", ".join(s.slug for s in cv.sections)
        return f"Section '{section}' not found. Available: {available}"
    return f"## {sec.heading}\n\n{sec.body}"


@mcp.resource("career-ops://report/{num}")
def get_report(num: str) -> str:
    """An evaluation report by zero-padded number (e.g. '012')."""
    text = rep_parser.read_report(REPORTS_DIR, num)
    if text is None:
        return f"Report {num.zfill(3)} not found in {REPORTS_DIR}"
    return text


# ── Prompts ──────────────────────────────────────────────────────────────────

@mcp.prompt()
def evaluate_fit(jd_url_or_text: str) -> str:
    """Generate a structured A-F job fit evaluation grounded in Eric's CV and past applications."""
    is_url = jd_url_or_text.strip().startswith("http")
    jd_ref = f"URL: {jd_url_or_text}" if is_url else "JD text provided below"
    jd_block = "" if is_url else f"\n\n---\n\n{jd_url_or_text}\n\n---"

    return f"""You are Eric's AI job search advisor. Evaluate the following job posting for fit.

{jd_ref}{jd_block}

## Steps

1. Call `match_cv_to_jd` with {'jd_url="' + jd_url_or_text + '"' if is_url else 'jd_text=(the JD text above)'} to get section-by-section CV match scores and gap analysis.
2. Call `search_applications_semantic` with a query based on the role title to find 3 similar past applications for score calibration.
3. Produce a structured evaluation in the standard career-ops report format below.

## Output Format

## Score: X.X/5

**URL:** {jd_url_or_text if is_url else 'N/A'}
**Date:** (today's date)
**Verification:** (is the posting likely live?)
**Legitimacy:** (Tier 1 / 2 / 3)

## A. CV Match
Use the per_section scores from match_cv_to_jd. Quote the top_bullets that align strongest.

## B. North Star Alignment
Does this role match Eric's target archetypes: Forward Deployed Engineer, Technical Account Manager, Applied AI / Solutions Architect?

## C. Compensation
Any visible comp data. If none, note it.

## D. Cultural Signals
Remote policy, visa sponsorship, company stage (seed/series/public), team size signals.

## E. Red Flags
Hard blockers: mandatory experience Eric lacks, auth requirements (US-only, no visa), geography mismatches.

## F. Global Score (X.X/5)
Weighted synthesis of A–E. Weights: CV Match 35%, North Star 25%, Comp 20%, Culture 10%, Red Flags 10%.

## G. Posting Legitimacy
Brief assessment of whether this is a real, live, non-ghosted posting.

## Verdict
One sentence: **Apply** / **Skip** / **Verify first** — and the single most important reason.
"""
