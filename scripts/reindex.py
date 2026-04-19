"""Force a full rebuild of the embeddings database.
Run with: uv run python scripts/reindex.py
"""
import os
os.environ["CAREER_OPS_MCP_REINDEX"] = "1"

from career_ops_mcp import storage

print("Rebuilding embeddings database...")
conn = storage.ensure_fresh()
count = conn.execute("SELECT COUNT(*) FROM docs").fetchone()[0]
print(f"Done. {count} documents indexed.")
