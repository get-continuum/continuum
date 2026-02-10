# Schema v0.2 Migration Plan

> **Status**: Planning  
> **Current Schema**: v0.1.0  
> **Target Schema**: v0.2.0  
> **Last Updated**: 2026-02-09

## 1. Overview

This document outlines the planned changes for the v0.2 Decision schema and the migration strategy for existing v0.1 data.

The v0.2 schema is a **non-breaking minor version bump** — all v0.1 decisions remain valid v0.2 decisions. New fields are optional with sensible defaults.

## 2. Planned Changes

### 2.1 New Fields

| Field | Type | Default | Rationale |
|-------|------|---------|-----------|
| `schema_version` | `string` | `"0.2.0"` | Explicit per-record schema version for forward compatibility. Currently only tracked at the schema level, not per decision. |
| `enforcement` | `object` | (structured) | Formalize the enforcement block as a proper nested object in the schema rather than using top-level `scope`/`decision_type`/`supersedes`/`precedence`/`override_policy` fields. This matches how the SDK already represents enforcement internally. |
| `tags` | `array[string]` | `[]` | Lightweight categorization beyond `decision_type`. Supports filtering and grouping (e.g., `["security", "api-design"]`). |
| `expires_at` | `string (date-time)` | `null` | Optional TTL for decisions that should auto-archive after a date. Useful for time-boxed experiments. |
| `source_ref` | `string` | `null` | Optional URI linking to the external source (PR, issue, Slack thread) that motivated the decision. |

### 2.2 Enforcement Object Consolidation

The v0.1 schema uses top-level fields for enforcement-related data:

```json
{
  "scope": "repo:acme/backend",
  "decision_type": "rejection",
  "supersedes": "dec_abc123",
  "precedence": 10,
  "override_policy": "invalid_by_default"
}
```

The v0.2 schema nests these under a single `enforcement` object:

```json
{
  "enforcement": {
    "scope": "repo:acme/backend",
    "decision_type": "rejection",
    "supersedes": "dec_abc123",
    "precedence": 10,
    "override_policy": "invalid_by_default"
  }
}
```

**Note**: The SDK's Pydantic model (`Enforcement`) already uses this nested structure internally. The schema change aligns the persisted JSON with the SDK representation.

### 2.3 Fields Under Consideration (Not Yet Confirmed)

| Field | Type | Discussion |
|-------|------|------------|
| `confidence` | `number (0-1)` | Useful for LLM-suggested decisions but may belong in `metadata` rather than the schema. |
| `review_state` | `string` | Tracks human review (`pending_review`, `approved`, `rejected`). Could overlap with `status`. |
| `related_decisions` | `array[string]` | Links to related (but not superseding) decisions. Graph complexity concern. |

## 3. Migration Strategy

### 3.1 Approach: Read-Time Auto-Upgrade

The SDK performs migration at **read time**, not write time. This avoids batch migrations and supports mixed-version stores.

```
v0.1 JSON on disk
       │
       ▼
  SDK reads file
       │
       ▼
  Detect schema_version
  (absent = v0.1)
       │
       ▼
  Apply migration function
  (v0.1 → v0.2)
       │
       ▼
  Return v0.2 Decision object
       │
       ▼
  On next write, persist as v0.2
```

### 3.2 Migration Function

```python
def migrate_v01_to_v02(data: dict) -> dict:
    """Upgrade a v0.1 decision dict to v0.2 format."""
    # Already v0.2 or later
    if data.get("schema_version", "").startswith("0.2"):
        return data

    migrated = {**data}

    # Add schema_version
    migrated["schema_version"] = "0.2.0"

    # Consolidate enforcement fields into nested object
    if "enforcement" not in migrated:
        enforcement = {}
        for field in ("scope", "decision_type", "supersedes", "precedence", "override_policy"):
            if field in migrated:
                enforcement[field] = migrated.pop(field)
        if enforcement:
            migrated["enforcement"] = enforcement

    # Add new optional fields with defaults
    migrated.setdefault("tags", [])
    migrated.setdefault("expires_at", None)
    migrated.setdefault("source_ref", None)

    return migrated
```

### 3.3 Backward Compatibility

- **v0.1 decisions remain valid**: The v0.2 schema accepts both top-level and nested enforcement fields during a transition period.
- **SDK accepts both formats**: The `ContinuumClient._load()` method detects the format and normalizes.
- **No batch migration required**: Existing stores upgrade gradually as decisions are read and re-written.

## 4. Testing Plan

### 4.1 Schema Validation Tests

Add to `oss/contracts/tests/`:

1. **v0.1 fixture files** — Existing example decisions (already in `examples/`).
2. **v0.2 fixture files** — New examples with `schema_version`, `enforcement` object, `tags`, etc.
3. **Migration round-trip test** — Load v0.1, migrate, validate against v0.2 schema, serialize, re-validate.
4. **Mixed-version store test** — Store with both v0.1 and v0.2 decisions; verify SDK reads both correctly.

### 4.2 SDK Tests

Add to `oss/sdk/python/tests/`:

1. **test_migration.py** — Unit tests for the `migrate_v01_to_v02` function.
2. **test_client_v02.py** — Integration tests verifying client handles mixed-version stores.

### 4.3 Compatibility Matrix

| Scenario | Expected Behavior |
|----------|-------------------|
| v0.2 SDK reads v0.1 decision | Auto-migrate on read, return v0.2 object |
| v0.2 SDK writes decision | Always writes v0.2 format |
| v0.1 SDK reads v0.2 decision | `additionalProperties: false` in v0.1 schema would reject. Document this as a known limitation; recommend upgrading SDK first. |
| Mixed v0.1/v0.2 store | v0.2 SDK handles transparently |

## 5. Rollout Plan

1. **Phase 1**: Implement migration function + tests (no schema file changes yet)
2. **Phase 2**: Publish `decision.v0.2.schema.json` alongside v0.1
3. **Phase 3**: SDK defaults to writing v0.2 format
4. **Phase 4**: Deprecation notice for v0.1 format (one minor version cycle)
5. **Phase 5**: v0.1 support removed in v0.3.0

## 6. Open Questions

- Should `enforcement` be required in v0.2? Currently optional in v0.1, and some decisions (pure interpretations) may not need enforcement at all.
- Should `schema_version` live inside the JSON file or be inferred from the file path/directory structure?
- Timeline for v0.2 freeze — target: after at least 2 weeks of v0.1 production usage.
