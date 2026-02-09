# OSS Boundary

This document details the boundary between the open-source (`oss/`) and proprietary (`core/`) layers. For the canonical reference, see [`BOUNDARY.md`](../../BOUNDARY.md) at the repository root.

## Guiding Principle

The OSS layer provides **deterministic, auditable logic**. No heuristics, no ML, no LLM calls. Extension points (abstract base classes) allow plugging in proprietary implementations from `core/`.

## What Lives in OSS

| Component | Location | Description |
|-----------|----------|-------------|
| Contracts | `oss/contracts/` | JSON Schemas, SPEC.md, examples, validation tests |
| SDK | `oss/sdk/python/` | Pydantic models, schema loader, lifecycle state machine, local CRUD client |
| Hooks | `oss/sdk/python/src/continuum/hooks.py` | ABCs: `AmbiguityScorer`, `DecisionCompiler`, `RiskScorer` |
| Enforcement | `oss/sdk/python/src/continuum/enforce/` | Deterministic rule engine: block/confirm/allow |
| Resolve | `oss/sdk/python/src/continuum/resolve/` | Basic flow: check prior decision, return context or needs_clarification |
| CLI | `oss/cli/` | Inspector: inspect, commit, supersede, scopes |
| MCP Server | `oss/mcp-server/` | Tool stubs for inspect/resolve/enforce/commit |
| Integrations | `oss/integrations/` | LangGraph nodes, LlamaIndex adapter stubs |
| Packs | `oss/packs/` | Decision templates (JSON) |

## What Lives in Core

| Component | Location | Description |
|-----------|----------|-------------|
| AmbiguityScorer | `core/src/continuum_engine/scorers/ambiguity.py` | LLM-based scoring + heuristic fallback |
| RiskScorer | `core/src/continuum_engine/scorers/risk.py` | LLM-based risk assessment + scope heuristics |
| DecisionCompiler | `core/src/continuum_engine/compiler/` | LLM-based rule extraction from rationale |
| Advanced Policies | `core/src/continuum_engine/enforcement/policies.py` | Gradual rollout, team-scoped, override approval, temporal decay |
| Intent Resolver | `core/src/continuum_engine/resolution/intent_resolver.py` | Memory-hit + candidate matching + ambiguity detection |
| Context Resolver | `core/src/continuum_engine/resolution/context_resolver.py` | Overlay-based resolution with selector matching |
| LLM Layer | `core/src/continuum_engine/llm/` | OpenAI/Anthropic client, prompt templates |

## Rules

1. **Never** add scoring heuristics, ML models, or LLM calls to `oss/`.
2. Extension points go as ABCs in `oss/sdk/python/src/continuum/hooks.py`; implementations go in `core/`.
3. `core/` may import from `continuum` (the OSS SDK). `oss/` must **never** import from `continuum_engine`.
4. The PR template includes a boundary checklist to enforce this at review time.

## How to Check

Before submitting a PR that touches `oss/`:

```bash
# Ensure no imports from the engine
rg "continuum_engine" oss/
# Should return zero results
```

If you're unsure whether a feature belongs in `oss/` or `core/`, ask: _"Does this require an LLM call or learned heuristic?"_ If yes, it goes in `core/`.
