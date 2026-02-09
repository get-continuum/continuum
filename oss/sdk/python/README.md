# Continuum Python SDK

Deterministic Python SDK for working with Continuum decision contracts.

## Install

```bash
pip install continuum-sdk
```

## Features

- Pydantic v2 models mirroring contract schemas
- Schema loader and validator
- Deterministic lifecycle state machine
- Local-file CRUD client
- Abstract hooks for extension (AmbiguityScorer, DecisionCompiler, RiskScorer)
