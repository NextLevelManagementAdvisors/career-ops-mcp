from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

import numpy as np
import sqlite_vec

from career_ops_mcp.config import CACHE_DIR, DB_PATH, REINDEX
from career_ops_mcp import embeddings as emb_mod
from career_ops_mcp.config import (
    CAREER_OPS_ROOT,
    CV_FILE,
    APPLICATIONS_FILE,
    REPORTS_DIR,
)
from career_ops_mcp.text import split_h2_sections, slugify


def _serialize(vec: np.ndarray) -> bytes:
    return sqlite_vec.serialize_float32(vec.astype(np.float32).tolist())


def _connect() -> sqlite3.Connection:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    conn.execute("PRAGMA journal_mode=WAL")
    _create_schema(conn)
    return conn


def _create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS docs (
            id INTEGER PRIMARY KEY,
            doc_id TEXT UNIQUE NOT NULL,
            kind TEXT NOT NULL,
            source_path TEXT NOT NULL,
            source_mtime REAL NOT NULL,
            content_hash TEXT NOT NULL,
            text TEXT NOT NULL,
            meta TEXT DEFAULT '{}'
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS docs_vec USING vec0(
            embedding FLOAT[384]
        );
    """)
    conn.commit()


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _upsert(conn: sqlite3.Connection, doc_id: str, kind: str, source_path: str,
            source_mtime: float, text: str, meta: dict) -> None:
    h = _content_hash(text)
    cur = conn.execute("SELECT id, content_hash FROM docs WHERE doc_id = ?", [doc_id])
    row = cur.fetchone()

    if row and row[1] == h:
        # Only mtime changed but content is same — update mtime only
        conn.execute(
            "UPDATE docs SET source_mtime = ? WHERE id = ?",
            [source_mtime, row[0]],
        )
        conn.commit()
        return

    vec = emb_mod.encode_one(text)
    blob = _serialize(vec)
    meta_json = json.dumps(meta)

    if row:
        row_id = row[0]
        conn.execute(
            "UPDATE docs SET source_mtime=?, content_hash=?, text=?, meta=?, source_path=? WHERE id=?",
            [source_mtime, h, text, meta_json, source_path, row_id],
        )
        conn.execute("DELETE FROM docs_vec WHERE rowid = ?", [row_id])
        conn.execute("INSERT INTO docs_vec(rowid, embedding) VALUES (?, ?)", [row_id, blob])
    else:
        cur2 = conn.execute(
            "INSERT INTO docs (doc_id, kind, source_path, source_mtime, content_hash, text, meta) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            [doc_id, kind, source_path, source_mtime, h, text, meta_json],
        )
        row_id = cur2.lastrowid
        conn.execute("INSERT INTO docs_vec(rowid, embedding) VALUES (?, ?)", [row_id, blob])

    conn.commit()


def _should_refresh(conn: sqlite3.Connection, doc_id: str, mtime: float) -> bool:
    cur = conn.execute("SELECT source_mtime FROM docs WHERE doc_id = ?", [doc_id])
    row = cur.fetchone()
    return row is None or row[0] != mtime


def refresh_cv(conn: sqlite3.Connection) -> None:
    if not CV_FILE.exists():
        return
    mtime = CV_FILE.stat().st_mtime
    text = CV_FILE.read_text(encoding="utf-8")
    sections = split_h2_sections(text)

    for heading_slug, body in sections.items():
        if not body.strip():
            continue
        doc_id = f"cv:section:{heading_slug}"
        if not REINDEX and not _should_refresh(conn, doc_id, mtime):
            continue
        _upsert(conn, doc_id, "cv_section", str(CV_FILE), mtime, body,
                {"slug": heading_slug, "source": "cv"})


def refresh_applications(conn: sqlite3.Connection) -> None:
    if not APPLICATIONS_FILE.exists():
        return
    mtime = APPLICATIONS_FILE.stat().st_mtime
    from career_ops_mcp.parsers import applications as app_parser
    apps = app_parser.parse(APPLICATIONS_FILE)
    for app in apps:
        doc_id = f"application:{app.num}"
        if not REINDEX and not _should_refresh(conn, doc_id, mtime):
            continue
        text = f"{app.company} — {app.role}\n{app.notes}"
        _upsert(conn, doc_id, "application", str(APPLICATIONS_FILE), mtime, text,
                app.to_dict())


def refresh_reports(conn: sqlite3.Connection) -> None:
    if not REPORTS_DIR.exists():
        return
    from career_ops_mcp.parsers import reports as rep_parser
    for meta in rep_parser.list_reports(REPORTS_DIR):
        mtime = meta.path.stat().st_mtime
        doc_id = f"report:{meta.num}"
        if not REINDEX and not _should_refresh(conn, doc_id, mtime):
            continue
        text = meta.path.read_text(encoding="utf-8")
        _upsert(conn, doc_id, "report", str(meta.path), mtime, text, meta.to_dict())


def ensure_fresh() -> sqlite3.Connection:
    conn = _connect()
    refresh_cv(conn)
    refresh_applications(conn)
    refresh_reports(conn)
    return conn


def knn_search(conn: sqlite3.Connection, query_vec: np.ndarray, top_k: int = 5,
               kind_filter: str | None = None) -> list[dict[str, Any]]:
    blob = _serialize(query_vec)
    rows = conn.execute(
        "SELECT rowid, distance FROM docs_vec WHERE embedding MATCH ? AND k = ?",
        [blob, top_k * 3 if kind_filter else top_k],
    ).fetchall()

    if not rows:
        return []

    row_ids = [r[0] for r in rows]
    distances = {r[0]: r[1] for r in rows}
    placeholders = ",".join(["?"] * len(row_ids))
    docs = conn.execute(
        f"SELECT id, doc_id, kind, text, meta FROM docs WHERE id IN ({placeholders})",
        row_ids,
    ).fetchall()

    results = []
    for doc in docs:
        doc_id_val, kind, text, meta_json = doc[1], doc[2], doc[3], doc[4]
        if kind_filter and kind != kind_filter:
            continue
        meta = json.loads(meta_json) if meta_json else {}
        results.append({
            "doc_id": doc_id_val,
            "kind": kind,
            "distance": distances[doc[0]],
            "similarity": max(0.0, 1.0 - distances[doc[0]]),
            "text": text,
            "meta": meta,
        })
        if len(results) >= top_k:
            break

    results.sort(key=lambda x: x["distance"])
    return results
