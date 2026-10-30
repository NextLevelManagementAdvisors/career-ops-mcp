from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from career_ops_mcp.config import CAREER_OPS_ROOT, CV_FILE, REPORTS_DIR
from career_ops_mcp.parsers import cv as cv_parser
from career_ops_mcp.parsers import reports as rep_parser
from career_ops_mcp import tools
from career_ops_mcp.profile import owner_name, possessive, target_archetypes

mcp = FastMCP(
    "career-ops",
    instructions=(
        f"Read-only access to {possessive(owner_name())} job search data from career-ops. "
        f"Data source: {CAREER_OPS_ROOT}. Tools for querying applications, "
        "semantic search, CV↔JD matching, pipeline, portals, and states."
    ),
)


# ── Tools ────────────────────────────────────────────────────────────────────

@mcp.tool(annotations=ToolAnnotations(title="List applications", readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False))
def list_applications(
    status: str | None = None,
    company: str | None = None,
    since: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """List tracked job applications. Filter by status, company substring, or ISO date (since)."""
    return tools.list_applications(status=status, company=company, since=since, limit=limit)


@mcp.tool(annotations=ToolAnnotations(title="Get application", readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False))
def get_application(company: str, role: str | None = None) -> dict | list[dict]:
    """Get detail for a specific application by company name. Returns the evaluation report if available."""
    return tools.get_application(company=company, role=role)


@mcp.tool(annotations=ToolAnnotations(title="Semantic search", readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False))
def search_applications_semantic(query: str, top_k: int = 5) -> list[dict]:
    """Semantic search over applications, reports, and CV sections using local embeddings."""
    return tools.search_applications_semantic(query=query, top_k=top_k)


@mcp.tool(annotations=ToolAnnotations(title="Match CV to JD", readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True))
def match_cv_to_jd(
    jd_text: str | None = None,
    jd_url: str | None = None,
    report_id: str | None = None,
) -> dict:
    """Score the user's CV against a JD. Returns per-section scores, top matching bullets, and gap hints.
    Provide one of: jd_text (pasted), jd_url (fetched), or report_id (e.g. '012')."""
    return tools.match_cv_to_jd(jd_text=jd_text, jd_url=jd_url, report_id=report_id)


@mcp.tool(annotations=ToolAnnotations(title="List portals", readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False))
def list_portals(enabled_only: bool = True, company: str | None = None) -> list[dict]:
    """List companies configured in the career-ops portal scanner."""
    return tools.list_portals(enabled_only=enabled_only, company=company)


@mcp.tool(annotations=ToolAnnotations(title="List pipeline", readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False))
def list_pipeline(bucket: str = "pending", limit: int = 100) -> list[dict]:
    """List entries in the evaluation pipeline. Buckets: pending, processed, pendientes."""
    return tools.list_pipeline(bucket=bucket, limit=limit)


@mcp.tool(annotations=ToolAnnotations(title="List states", readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False))
def list_states() -> list[dict]:
    """List canonical application statuses and their aliases."""
    return tools.list_states()


# ── Resources ────────────────────────────────────────────────────────────────

@mcp.resource("career-ops://cv")
def get_cv() -> str:
    """The user's full canonical CV/resume (cv.md)."""
    if not CV_FILE.exists():
        return f"cv.md not found at {CV_FILE}"
    return CV_FILE.read_text(encoding="utf-8")


@mcp.resource("career-ops://cv/{section}")
def get_cv_section(section: str) -> str:
    """A specific section of the user's CV by slug (e.g. professional-experience, technical-skills)."""
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
    """Generate a structured A-F job fit evaluation grounded in the user's CV and past applications."""
    is_url = jd_url_or_text.strip().startswith("http")
    jd_ref = f"URL: {jd_url_or_text}" if is_url else "JD text provided below"
    jd_block = "" if is_url else f"\n\n---\n\n{jd_url_or_text}\n\n---"

    owner = owner_name()
    poss = possessive(owner)
    archetypes = target_archetypes()
    if archetypes:
        north_star = f"Does this role match {poss} target archetypes: {', '.join(archetypes)}?"
    else:
        north_star = (
            f"Does this role match {poss} target roles? No archetypes are configured "
            "(set target_roles in config/profile.yml), so infer them from the CV."
        )

    return f"""You are {poss} AI job search advisor. Evaluate the following job posting for fit.

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
{north_star}

## C. Compensation
Any visible comp data. If none, note it.

## D. Cultural Signals
Remote policy, visa sponsorship, company stage (seed/series/public), team size signals.

## E. Red Flags
Hard blockers: mandatory experience {owner} lacks, work-authorization or visa requirements, geography mismatches.

## F. Global Score (X.X/5)
Weighted synthesis of A–E. Weights: CV Match 35%, North Star 25%, Comp 20%, Culture 10%, Red Flags 10%.

## G. Posting Legitimacy
Brief assessment of whether this is a real, live, non-ghosted posting.

## Verdict
One sentence: **Apply** / **Skip** / **Verify first** — and the single most important reason.
"""
