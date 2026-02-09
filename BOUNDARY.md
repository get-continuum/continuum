# OSS vs Core Boundary

This document defines what belongs in `oss/` (Apache-2.0) versus `core/` (BSL-1.1).

## Principle

The OSS layer provides **deterministic, auditable logic**. No heuristics, no ML, no LLM calls. Extension points (abstract base classes) allow plugging in proprietary implementations from `core/`.

## OSS layer (`oss/`, Apache-2.0)

| Component | What ships | Location |
|-----------|-----------|----------|
| Contracts | JSON Schemas, SPEC.md, examples, validation tests | `oss/contracts/` |
| SDK | Pydantic models, schema loader, lifecycle state machine, local CRUD client | `oss/sdk/python/` |
| Hooks | ABCs: `AmbiguityScorer`, `DecisionCompiler`, `RiskScorer` | `oss/sdk/python/src/continuum/hooks.py` |
| Enforcement | Deterministic rule engine: block/confirm/allow | `oss/sdk/python/src/continuum/enforce/` |
| Resolve | Basic flow: check prior decision, return needs_clarification or resolved_context | `oss/sdk/python/src/continuum/resolve/` |
| CLI | Inspector: inspect, commit, supersede, scopes | `oss/cli/` |
| MCP Server | Tool stubs for inspect/resolve/enforce/commit | `oss/mcp-server/` |
| Integrations | LangGraph nodes, LlamaIndex adapter stubs | `oss/integrations/` |
| Packs | Decision templates (JSON) | `oss/packs/` |

## Core layer (`core/`, BSL-1.1)

| Component | What ships | Location |
|-----------|-----------|----------|
| AmbiguityScorer | LLM-based scoring + heuristic fallback | `core/src/continuum_engine/scorers/ambiguity.py` |
| RiskScorer | LLM-based risk assessment + scope heuristics | `core/src/continuum_engine/scorers/risk.py` |
| DecisionCompiler | LLM-based rule extraction from rationale | `core/src/continuum_engine/compiler/` |
| Advanced Policies | Gradual rollout, team-scoped, override approval, temporal decay | `core/src/continuum_engine/enforcement/policies.py` |
| Intent Resolver | Memory-hit + candidate + context matching + ambiguity detection | `core/src/continuum_engine/resolution/intent_resolver.py` |
| Context Resolver | Overlay-based resolution with selector matching | `core/src/continuum_engine/resolution/context_resolver.py` |
| LLM Layer | OpenAI/Anthropic client, prompt templates | `core/src/continuum_engine/llm/` |

## Rules

1. **Never** add scoring heuristics, ML models, or LLM calls to `oss/`.
2. Extension points go as ABCs in `oss/sdk/python/src/continuum/hooks.py`; implementations go in `core/`.
3. `core/` may import from `continuum` (the OSS SDK). `oss/` must **never** import from `continuum_engine`.
4. PR template includes a boundary checklist.
