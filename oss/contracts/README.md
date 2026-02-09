# Continuum Contracts

Decision contract schemas, specification, and validation tests for the Continuum platform.

## Overview

Contracts define the structure and lifecycle of **Decisions** — the core unit of institutional knowledge in Continuum. A Decision captures what was decided, why, what alternatives were considered, and how the decision should be enforced.

## Directory Structure

```
contracts/
├── README.md                  # This file
├── SPEC.md                    # Human-readable specification
├── schemas/
│   ├── decision.v0.schema.json          # Main Decision JSON Schema
│   ├── decision-status.v0.schema.json   # Status enum & transition rules
│   └── context.v0.schema.json           # Context object schema
├── examples/
│   ├── valid-code-decision.json         # Valid: reject MongoDB for PostgreSQL
│   ├── valid-interpretation-decision.json # Valid: define "revenue" meaning
│   ├── invalid-missing-required.json    # Invalid: missing required fields
│   └── invalid-bad-transition.json      # Invalid: bad enum value
└── tests/
    ├── conftest.py                      # Shared pytest fixtures
    └── test_schema_validation.py        # Schema validation tests
```

## Quick Start

### Validate examples against schemas

```bash
cd oss/contracts
python -m pytest tests/ -v
```

### Dependencies

- Python 3.9+
- `jsonschema` (for JSON Schema validation in tests)
- `pytest` (test runner)

```bash
pip install jsonschema pytest
```

## Schema Version

Current schema version: **0.1.0** (draft)

All schemas use [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12/schema).

## Key Concepts

- **Decision**: A recorded decision with rationale, options considered, and enforcement rules.
- **Status Lifecycle**: `draft` → `active` → `superseded` → `archived`
- **Scope**: Where a decision applies (repo, folder, user, workflow, team).
- **Decision Types**: `interpretation`, `rejection`, `preference`, `behavior_rule`
- **Override Policy**: What happens when a rejected option is used (`invalid_by_default`, `warn`, `allow`).

## License

See the root [LICENSE](../../LICENSE) file for details.
