# career-ops-mcp

A read-only MCP (Model Context Protocol) server that exposes [career-ops](https://github.com/thecyprince/career-ops) job-search data to any MCP-compatible AI client — Claude Desktop, Claude Code, or any future MCP client.

The novel core: **local semantic search** over applications, evaluation reports, and CV sections using [fastembed](https://github.com/qdrant/fastembed) (ONNX-based, no PyTorch) with [sqlite-vec](https://github.com/asg017/sqlite-vec) as the vector store.

## What it does

Exposes 7 tools, 3 resources, and 1 prompt:

### Tools

| Tool | What it does |
|------|-------------|
| `list_applications` | Filter the tracker by status, company, or date |
| `get_application` | Get full detail + evaluation report for a company |
| `search_applications_semantic` | Find similar applications/reports using embeddings |
| `match_cv_to_jd` | Score CV sections against a JD, return gap analysis + top matching bullets |
| `list_portals` | List companies in the portal scanner config |
| `list_pipeline` | See pending evaluation URLs |
| `list_states` | Show canonical application statuses |

### Resources

- `career-ops://cv` — full CV
- `career-ops://cv/{section}` — CV section by slug (e.g. `professional-experience`)
- `career-ops://report/{num}` — evaluation report by number (e.g. `012`)

### Prompt

- `evaluate_fit(jd_url_or_text)` — instructs the AI to call `match_cv_to_jd` + `search_applications_semantic` and produce a structured A–F evaluation report

## Why this is interesting (for recruiters)

- **MCP server design** — demonstrates tool schema design, resource/prompt separation, and understanding of how LLMs use tools
- **Local ONNX embeddings** — sentence-level semantic retrieval without a cloud API, using `BAAI/bge-small-en-v1.5`
- **sqlite-vec** — vector store in a single SQLite file with mtime-based freshness tracking; no external infrastructure
- **Dogfooded** — built on top of an active job-search system with 80+ tracked companies and 12+ evaluation reports

## Prerequisites

- Python 3.13 (managed by `uv`)
- [uv](https://github.com/astral-sh/uv): `brew install uv`
- [career-ops](https://github.com/santifer/career-ops) at `~/Projects/career-ops` (or set `CAREER_OPS_ROOT`)

## Install

```bash
git clone https://github.com/thecyprince/career-ops-mcp ~/Projects/career-ops-mcp
cd ~/Projects/career-ops-mcp
uv sync
```

The first run will download the embedding model (~40MB) to `~/.cache/fastembed/`.

## Connect to Claude Code

```bash
claude mcp add career-ops --scope user -- \
  uv --directory ~/Projects/career-ops-mcp run career-ops-mcp
```

Set `CAREER_OPS_ROOT` if your career-ops repo is elsewhere:

```bash
claude mcp add career-ops --scope user \
  --env CAREER_OPS_ROOT=~/path/to/career-ops \
  -- uv --directory ~/Projects/career-ops-mcp run career-ops-mcp
```

## Connect to Claude Desktop

Merge this into `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "career-ops": {
      "command": "/opt/homebrew/bin/uv",
      "args": ["--directory", "~/Projects/career-ops-mcp", "run", "career-ops-mcp"],
      "env": { "CAREER_OPS_ROOT": "~/Projects/career-ops" }
    }
  }
}
```

Quit and relaunch Claude Desktop.

## Test

```bash
# Unit tests (fast, no model download)
uv run pytest

# Smoke test (requires model download on first run)
CAREER_OPS_ROOT=~/Projects/career-ops uv run python scripts/smoke.py

# Interactive exploration via MCP Inspector
npx @modelcontextprotocol/inspector \
  uv --directory ~/Projects/career-ops-mcp run career-ops-mcp
```

## Architecture

```
career-ops/                  (data source, read-only)
  cv.md                      → parsed into CV sections for embeddings
  data/applications.md       → parsed as structured application records
  reports/NNN-*.md           → indexed as full-text documents for semantic search
  data/pipeline.md           → pending evaluation URLs
  templates/states.yml       → canonical status definitions
  portals.yml                → 88+ company scanner configs

career-ops-mcp/
  src/career_ops_mcp/
    server.py                FastMCP server (tools, resources, prompts)
    tools.py                 Pure functions behind each tool
    matching.py              CV↔JD cosine similarity with per-section breakdown
    embeddings.py            fastembed BAAI/bge-small-en-v1.5 wrapper
    storage.py               sqlite-vec schema, mtime freshness, KNN search
    parsers/                 One parser per data file type
    text.py                  Markdown section splitter, bullet extractor

~/.cache/career-ops-mcp/
  embeddings.db              SQLite + sqlite-vec vector store (auto-managed)
```

## Status & Roadmap

### v0.1 (current) — read-only adapter
- 7 tools: list/get applications, semantic search, CV↔JD match, portals, pipeline, states
- 3 resources: full CV, CV by section, evaluation report by number
- 1 prompt: `evaluate_fit` (A–F scored JD evaluation)
- Local ONNX embeddings (fastembed + sqlite-vec, 384-dim bge-small)
- stdio transport for Claude Desktop + Claude Code

### v0.2 — authoring prompts
- `cover_letter` prompt — drafts a cover letter grounded in CV + JD
- `interview_prep` prompt — generates STAR+R stories from a report + CV
- `compare_offers` prompt — multi-JD ranking against career goals
- Best-effort URL fetch in `match_cv_to_jd`

### v0.3 — cross-source intelligence
- Deduplication across pipeline.md + applications.md + scan-history.tsv
- Multilingual embedding model (for Korean/German/French postings)

### v1.0 — opt-in write operations
- `draft_application_entry` — writes to `batch/tracker-additions/` per career-ops data contract
- `add_pipeline_url` — appends to pipeline.md Pending bucket
- Dry-run mode by default; explicit flag to persist

### v1.x — external integrations
- Google Sheets ingestion, LinkedIn saved-jobs import, Gmail thread linking
- HTTP/SSE transport for remote access

## License

MIT
