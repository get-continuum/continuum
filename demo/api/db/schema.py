"""SQLite schema for the hosted Continuum API (MVP).

Tables:
  - workspaces: tenant isolation
  - api_keys: authentication
  - decisions: persisted decision records

This is a minimal MVP schema. For production, migrate to Postgres
and add decision_versions, audit_log, etc.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS workspaces (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS api_keys (
    id              TEXT PRIMARY KEY,
    workspace_id    TEXT NOT NULL REFERENCES workspaces(id),
    key_hash        TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL DEFAULT 'default',
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS decisions (
    id              TEXT PRIMARY KEY,
    workspace_id    TEXT NOT NULL REFERENCES workspaces(id),
    version         INTEGER NOT NULL DEFAULT 0,
    status          TEXT NOT NULL DEFAULT 'draft',
    title           TEXT NOT NULL,
    rationale       TEXT,
    scope           TEXT,
    decision_type   TEXT,
    supersedes      TEXT,
    precedence      INTEGER,
    override_policy TEXT NOT NULL DEFAULT 'invalid_by_default',
    payload_json    TEXT NOT NULL DEFAULT '{}',
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_decisions_workspace
    ON decisions(workspace_id);

CREATE INDEX IF NOT EXISTS idx_decisions_scope
    ON decisions(workspace_id, scope);

CREATE INDEX IF NOT EXISTS idx_decisions_status
    ON decisions(workspace_id, status);

CREATE INDEX IF NOT EXISTS idx_api_keys_hash
    ON api_keys(key_hash);

CREATE TABLE IF NOT EXISTS decision_evidence (
    id              TEXT PRIMARY KEY,
    decision_id     TEXT NOT NULL REFERENCES decisions(id),
    source_type     TEXT NOT NULL DEFAULT 'conversation',
    source_ref      TEXT NOT NULL DEFAULT '',
    span_start      INTEGER NOT NULL DEFAULT 0,
    span_end        INTEGER NOT NULL DEFAULT 0,
    quote           TEXT NOT NULL DEFAULT '',
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_evidence_decision
    ON decision_evidence(decision_id);

CREATE TABLE IF NOT EXISTS candidates (
    id              TEXT PRIMARY KEY,
    workspace_id    TEXT NOT NULL REFERENCES workspaces(id),
    payload_json    TEXT NOT NULL DEFAULT '{}',
    risk            TEXT NOT NULL DEFAULT 'medium',
    confidence      REAL NOT NULL DEFAULT 0.5,
    status          TEXT NOT NULL DEFAULT 'pending',
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_candidates_workspace
    ON candidates(workspace_id);

CREATE INDEX IF NOT EXISTS idx_candidates_status
    ON candidates(workspace_id, status);
"""


def init_db(db_path: str | Path = ".continuum/continuum.db") -> sqlite3.Connection:
    """Initialize the SQLite database and return a connection."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.executescript(SCHEMA_SQL)
    return conn
