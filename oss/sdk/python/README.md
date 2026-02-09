# Continuum Python SDK

Deterministic Python SDK for working with Continuum decision contracts.

## Install

```bash
pip install continuum-sdk
```

## Stable API (v0.1)

The primary entry point is `ContinuumClient`. These convenience methods are considered stable for v0.1:

- `inspect(scope)`: return the active binding set for a scope
- `resolve(query, scope, candidates=None)`: ambiguity gate (resolved vs needs_clarification)
- `enforce(action, scope)`: enforcement verdict for a proposed action
- `supersede(old_id, new_title, **kwargs)`: replace an active decision with a new one

## Features

- Pydantic v2 models mirroring contract schemas
- Schema loader and validator
- Deterministic lifecycle state machine
- Local-file CRUD client
- Abstract hooks for extension (AmbiguityScorer, DecisionCompiler, RiskScorer)
