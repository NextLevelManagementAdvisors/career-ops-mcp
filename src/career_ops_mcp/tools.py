from __future__ import annotations

from datetime import date as date_type

from career_ops_mcp.config import (
    APPLICATIONS_FILE,
    CV_FILE,
    PIPELINE_FILE,
    PORTALS_FILE,
    REPORTS_DIR,
    STATES_FILE,
)
from career_ops_mcp.parsers import applications as app_parser
from career_ops_mcp.parsers import pipeline as pipe_parser
from career_ops_mcp.parsers import portals as portal_parser
from career_ops_mcp.parsers import reports as rep_parser
from career_ops_mcp.parsers import states as states_parser
from career_ops_mcp import embeddings as emb_mod
from career_ops_mcp import storage, matching


def list_applications(
    status: str | None = None,
    company: str | None = None,
    since: str | None = None,
    limit: int = 50,
) -> list[dict]:
    if not APPLICATIONS_FILE.exists():
        return []
    apps = app_parser.parse(APPLICATIONS_FILE)
    result = []
    for app in apps:
        if status and app.status.lower() != status.lower():
            continue
        if company and company.lower() not in app.company.lower():
            continue
        if since and app.date < since:
            continue
        result.append(app.to_dict())
        if len(result) >= limit:
            break
    return result


def get_application(company: str, role: str | None = None) -> dict | list[dict]:
    if not APPLICATIONS_FILE.exists():
        return {"error": f"applications.md not found at {APPLICATIONS_FILE}"}
    apps = app_parser.parse(APPLICATIONS_FILE)
    matches = [a for a in apps if company.lower() in a.company.lower()]
    if role:
        matches = [a for a in matches if role.lower() in a.role.lower()]

    if len(matches) == 0:
        return {"error": f"No application found for '{company}'"}
    if len(matches) > 1 and not role:
        return [a.to_dict() for a in matches]

    app = matches[0]
    result = app.to_dict()
    if app.report_num:
        report_text = rep_parser.read_report(REPORTS_DIR, app.report_num)
        if report_text:
            result["report_markdown"] = report_text
    return result


def search_applications_semantic(query: str, top_k: int = 5) -> list[dict]:
    conn = storage.ensure_fresh()
    query_vec = emb_mod.encode_one(query)
    hits = storage.knn_search(conn, query_vec, top_k=top_k)

    results = []
    for hit in hits:
        meta = hit["meta"]
        if hit["kind"] == "report":
            results.append({
                "type": "report",
                "num": meta.get("num"),
                "slug": meta.get("slug"),
                "similarity": hit["similarity"],
                "excerpt": hit["text"][:300].replace("\n", " "),
            })
        elif hit["kind"] == "application":
            results.append({
                "type": "application",
                "num": meta.get("num"),
                "company": meta.get("company"),
                "role": meta.get("role"),
                "score": meta.get("score"),
                "similarity": hit["similarity"],
                "excerpt": hit["text"][:200],
            })
        elif hit["kind"] == "cv_section":
            results.append({
                "type": "cv_section",
                "slug": meta.get("slug"),
                "similarity": hit["similarity"],
                "excerpt": hit["text"][:200],
            })
    return results


def match_cv_to_jd(
    jd_text: str | None = None,
    jd_url: str | None = None,
    report_id: str | None = None,
) -> dict:
    text = jd_text
    if not text and report_id:
        text = rep_parser.read_report(REPORTS_DIR, report_id)
    if not text and jd_url:
        try:
            import urllib.request, urllib.parse, socket, ipaddress
            parsed = urllib.parse.urlparse(jd_url)
            if parsed.scheme not in ("http", "https"):
                return {"error": "refused: jd_url must be http(s)"}
            host = parsed.hostname or ""
            for info in socket.getaddrinfo(host, None):
                ip = ipaddress.ip_address(info[4][0])
                if (ip.is_private or ip.is_loopback or ip.is_link_local
                        or ip.is_reserved or ip.is_multicast or ip.is_unspecified):
                    return {"error": "refused: jd_url resolves to a non-public address"}
            with urllib.request.urlopen(jd_url, timeout=10) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
            import re
            text = re.sub(r"<[^>]+>", " ", raw)
            text = re.sub(r"\s+", " ", text).strip()
        except Exception as e:
            return {"error": f"Could not fetch URL: {e}"}
    if not text:
        return {"error": "Provide jd_text, jd_url, or report_id"}
    return matching.match_cv_to_jd(text)


def list_portals(enabled_only: bool = True, company: str | None = None) -> list[dict]:
    if not PORTALS_FILE.exists():
        return []
    portals = portal_parser.parse(PORTALS_FILE)
    result = []
    for p in portals:
        if enabled_only and not p.enabled:
            continue
        if company and company.lower() not in p.name.lower():
            continue
        result.append(p.to_dict())
    return result


def list_pipeline(bucket: str = "pending", limit: int = 100) -> list[dict]:
    if not PIPELINE_FILE.exists():
        return []
    all_buckets = pipe_parser.parse(PIPELINE_FILE)
    entries = all_buckets.get(bucket.lower(), [])
    return [e.to_dict() for e in entries[:limit]]


def list_states() -> list[dict]:
    if not STATES_FILE.exists():
        return []
    index = states_parser.parse(STATES_FILE)
    return [s.to_dict() for s in index.states]
