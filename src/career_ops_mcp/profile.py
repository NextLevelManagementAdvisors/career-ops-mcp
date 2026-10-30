"""Owner identity and target roles for this career-ops workspace.

Each value resolves in this order: environment variable, then
CAREER_OPS_ROOT/config/profile.yml (the same file career-ops itself uses),
then a neutral default. Values are read on every call, so editing profile.yml
takes effect without a restart, except for text frozen into the MCP server
instructions at import time.
"""
from __future__ import annotations

import os
from pathlib import Path

import yaml

from career_ops_mcp.config import PROFILE_FILE

DEFAULT_OWNER = "the user"


def _load(path: Path) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {}
    return data if isinstance(data, dict) else {}


def owner_name(path: Path | None = None) -> str:
    """Env CAREER_OPS_OWNER_NAME, else candidate.full_name, else "the user"."""
    env = os.environ.get("CAREER_OPS_OWNER_NAME", "").strip()
    if env:
        return env
    candidate = _load(path or PROFILE_FILE).get("candidate")
    if isinstance(candidate, dict):
        name = candidate.get("full_name")
        if isinstance(name, str) and name.strip():
            return name.strip()
    return DEFAULT_OWNER


def possessive(name: str) -> str:
    return f"{name}'" if name.endswith("s") else f"{name}'s"


def target_archetypes(path: Path | None = None) -> list[str]:
    """Env CAREER_OPS_ARCHETYPES (comma-separated), else target_roles.archetypes
    names, else target_roles.primary, else an empty list."""
    env = os.environ.get("CAREER_OPS_ARCHETYPES", "")
    items = [s.strip() for s in env.split(",") if s.strip()]
    if items:
        return items
    roles = _load(path or PROFILE_FILE).get("target_roles")
    if not isinstance(roles, dict):
        return []
    names: list[str] = []
    for a in roles.get("archetypes") or []:
        if isinstance(a, dict):
            n = a.get("name")
            if isinstance(n, str) and n.strip():
                names.append(n.strip())
        elif isinstance(a, str) and a.strip():
            names.append(a.strip())
    if names:
        return names
    return [r.strip() for r in roles.get("primary") or [] if isinstance(r, str) and r.strip()]
