-- Continuum hosted backend – Postgres schema (Neon-compatible)
-- Run once against your Neon database to bootstrap the tables.

CREATE TABLE IF NOT EXISTS workspaces (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS users (
    id              TEXT PRIMARY KEY,
    email           TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    workspace_id    TEXT NOT NULL REFERENCES workspaces(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

CREATE TABLE IF NOT EXISTS api_keys (
    id              TEXT PRIMARY KEY,
    workspace_id    TEXT NOT NULL REFERENCES workspaces(id),
    key_hash        TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL DEFAULT 'default',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);

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
    payload_json    JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_decisions_workspace
    ON decisions(workspace_id);

CREATE INDEX IF NOT EXISTS idx_decisions_scope
    ON decisions(workspace_id, scope);

CREATE INDEX IF NOT EXISTS idx_decisions_status
    ON decisions(workspace_id, status);
