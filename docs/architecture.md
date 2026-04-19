# Architecture

## Data flow

```
MCP Client (Claude Desktop / Claude Code)
        │
        │  JSON-RPC over stdio
        ▼
career-ops-mcp server (FastMCP)
        │
        ├── list_applications ──► parsers/applications.py ──► career-ops/data/applications.md
        ├── get_application   ──► parsers/applications.py + parsers/reports.py
        ├── list_pipeline     ──► parsers/pipeline.py     ──► career-ops/data/pipeline.md
        ├── list_portals      ──► parsers/portals.py      ──► career-ops/portals.yml
        ├── list_states       ──► parsers/states.py       ──► career-ops/templates/states.yml
        │
        ├── search_applications_semantic ──► storage.py (knn_search)
        │                                        │
        │                                        ├── embeddings.db (sqlite-vec)
        │                                        └── embeddings.py (fastembed on freshness miss)
        │
        └── match_cv_to_jd ──► matching.py
                                    │
                                    ├── parsers/cv.py ──► career-ops/cv.md
                                    └── embeddings.py (fastembed)
```

## Embedding freshness

On each tool call that touches the vector store, `storage.ensure_fresh()` runs a **mtime check** for each source file:

1. `stat` each source file → compare `source_mtime` to DB value
2. If mtime changed → compute SHA-256 content hash
3. If hash changed → re-embed the document and upsert into sqlite-vec
4. If hash unchanged → only update mtime (no re-embedding)

This means embeddings stay current with no background daemon or polling.

## Embedding model

**BAAI/bge-small-en-v1.5** via fastembed (ONNX runtime):
- 384 dimensions
- ~33MB model size
- ~7ms per document on M-series Mac CPU
- Downloaded to `~/.cache/fastembed/` on first use
- No cloud API, no PyTorch, no CUDA required

## Why sqlite-vec

A vector store in a single SQLite file:
- Zero-setup: no server, no port, no config
- Survives across MCP sessions (embeddings persist between restarts)
- KNN search via `vec0` virtual table: `WHERE embedding MATCH ? AND k = N`
- Atomic upserts: safe for concurrent reads (WAL mode)
- Inspectable with any SQLite browser

## MCP design choices

**Tools vs resources vs prompts:**
- **Tools** = dynamic queries (filter, search, match) — the LLM calls these with arguments
- **Resources** = static documents (cv.md, a report) — the client can attach these to context
- **Prompts** = reusable templates (`evaluate_fit`) — the client instantiates these with the LLM

**Read-only for v0.1:** All writes stay in career-ops (the authoritative system). The MCP server is a pure read layer. This avoids state conflicts between the two systems.

**stdio transport:** Works identically for Claude Desktop and Claude Code. The server process is spawned per-session and communicates via stdin/stdout. No port binding, no auth.
