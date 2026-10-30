import os
from pathlib import Path

CAREER_OPS_ROOT = Path(
    os.environ.get("CAREER_OPS_ROOT", "~/Projects/career-ops")
).expanduser()

CACHE_DIR = Path(
    os.environ.get("CAREER_OPS_CACHE", "~/.cache/career-ops-mcp")
).expanduser()

DB_PATH = CACHE_DIR / "embeddings.db"
EMBED_MODEL = "BAAI/bge-small-en-v1.5"
REINDEX = os.environ.get("CAREER_OPS_MCP_REINDEX", "0") == "1"

APPLICATIONS_FILE = CAREER_OPS_ROOT / "data" / "applications.md"
CV_FILE = CAREER_OPS_ROOT / "cv.md"
PIPELINE_FILE = CAREER_OPS_ROOT / "data" / "pipeline.md"
STATES_FILE = CAREER_OPS_ROOT / "templates" / "states.yml"
PORTALS_FILE = CAREER_OPS_ROOT / "portals.yml"
REPORTS_DIR = CAREER_OPS_ROOT / "reports"
PROFILE_FILE = CAREER_OPS_ROOT / "config" / "profile.yml"
