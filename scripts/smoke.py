"""Quick end-to-end smoke test for all MCP tools.
Run with: uv run python scripts/smoke.py
Exits with code 1 if any tool fails.
"""
import os
import sys
from pathlib import Path

# Point at real career-ops data if available
DEFAULT_ROOT = Path("~/Projects/career-ops").expanduser()
os.environ.setdefault("CAREER_OPS_ROOT", str(DEFAULT_ROOT))

import career_ops_mcp.tools as tools

CHECKS = []


def check(name: str, fn, *args, **kwargs):
    try:
        result = fn(*args, **kwargs)
        status = "ok"
        detail = repr(result)[:120]
    except Exception as e:
        status = "FAIL"
        detail = str(e)
    CHECKS.append((name, status, detail))
    symbol = "✓" if status == "ok" else "✗"
    print(f"  {symbol} {name}: {detail}")
    return status == "ok"


print("career-ops-mcp smoke test")
print("=" * 50)

check("list_applications (all)", tools.list_applications)
check("list_applications (status filter)", tools.list_applications, status="Evaluated")
check("list_applications (company filter)", tools.list_applications, company="Anthropic")
check("get_application (company)", tools.get_application, "Anthropic")
check("list_states", tools.list_states)
check("list_pipeline (pending)", tools.list_pipeline, bucket="pending")
check("list_portals (enabled)", tools.list_portals, enabled_only=True)
check("list_portals (company)", tools.list_portals, company="Anthropic")

print("\n  [semantic search requires model download on first run]")
check("search_applications_semantic", tools.search_applications_semantic,
      query="Forward Deployed Engineer AI", top_k=3)

print("\n  [match_cv_to_jd also requires model]")
check("match_cv_to_jd (text)", tools.match_cv_to_jd,
      jd_text="We are looking for a Solutions Architect with API integration and LLM experience.")

print()
passed = sum(1 for _, s, _ in CHECKS if s == "ok")
failed = sum(1 for _, s, _ in CHECKS if s != "ok")
print(f"Results: {passed} passed, {failed} failed")

if failed:
    print("SMOKE TEST FAILED")
    sys.exit(1)
else:
    print("All checks passed.")
