-- Add binding_key, key, and value_hash columns for idempotent commit
-- and auto-supersede support.  Run after 001_init.sql.

ALTER TABLE decisions ADD COLUMN IF NOT EXISTS key TEXT;
ALTER TABLE decisions ADD COLUMN IF NOT EXISTS binding_key TEXT NOT NULL DEFAULT '';
ALTER TABLE decisions ADD COLUMN IF NOT EXISTS value_hash TEXT NOT NULL DEFAULT '';

-- Backfill existing rows: binding_key = COALESCE(key, title)
UPDATE decisions SET binding_key = COALESCE(key, title)
WHERE binding_key = '';

-- Enforce at most one active decision per (workspace, scope, binding_key)
CREATE UNIQUE INDEX IF NOT EXISTS uniq_active_binding
ON decisions(workspace_id, scope, binding_key)
WHERE status = 'active';
