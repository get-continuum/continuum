# Continuum Architecture

## What is Continuum?

Continuum is a **Decision Control Plane for AI Agents**. It captures, enforces, and resolves decisions so AI agents behave consistently across prompts, sessions, and teams.

Instead of letting each agent prompt produce unpredictable, context-free outputs, Continuum gives agents a structured memory of past decisions and a deterministic enforcement layer that ensures consistency.

## Core Concepts

### Decisions

A **Decision** is the atomic unit. It records what was decided, why, which options were considered, and what was rejected. Decisions are immutable once committed and are identified by a unique ID.

### Contracts

**Contracts** are JSON Schemas that define the shape of a valid Decision. They ensure every decision carries the required fields (title, scope, rationale, options, lifecycle status) and can be validated deterministically.

### Enforcement

The **Enforcement** layer applies deterministic rules to incoming actions. Given a decision's risk level and the action context, enforcement returns one of three verdicts: `allow`, `confirm` (human-in-the-loop), or `block`. No ML, no heuristics — pure rule evaluation.

### Resolve

The **Resolve** flow checks whether a prior decision already covers the current prompt. It returns either `resolved_context` (a matching decision was found) or `needs_clarification` (ambiguity detected, human input required).

### Scopes

**Scopes** are hierarchical identifiers (e.g., `repo:acme/backend`, `team:platform`) that determine where a decision applies. Scoping enables decisions to be reused across projects and teams.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        AI Agent / IDE                        │
│   (Cursor, Copilot, LangGraph pipeline, custom agent)       │
└────────────────────┬────────────────────────────────────────┘
                     │  prompt / action
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Continuum SDK (OSS)                        │
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────┐ │
│  │  Resolve  │  │ Enforce  │  │  Commit  │  │   Inspect   │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬──────┘ │
│       │              │              │               │         │
│  ┌────▼──────────────▼──────────────▼───────────────▼──────┐ │
│  │              Decision Store (local JSON / API)           │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                     │
                     │  hooks (ABCs)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Continuum Engine (Core)                      │
│                                                               │
│  ┌────────────────┐  ┌───────────────┐  ┌────────────────┐  │
│  │ AmbiguityScorer│  │DecisionCompiler│  │  RiskScorer    │  │
│  │   (LLM-based)  │  │  (LLM-based)  │  │  (LLM-based)  │  │
│  └────────────────┘  └───────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## OSS vs Core Boundary

| Layer | License | Contains |
|-------|---------|----------|
| `oss/` | Apache-2.0 | Contracts, SDK, CLI, MCP server, integrations, packs — all deterministic |
| `core/` | BSL-1.1 | LLM-based scorers, compiler, advanced policies, intent resolver |

The OSS layer **never** imports from `core/`. Extension points are defined as abstract base classes (ABCs) in the SDK's `hooks.py`. Core provides implementations. See [BOUNDARY.md](../../BOUNDARY.md) for the full specification.

## Data Flow

```
prompt  ──►  resolve()  ──►  enforce()  ──►  commit()
               │                 │                │
        check prior        apply rules       persist
        decisions          (allow/confirm/    decision
                            block)
```

1. **Resolve**: The agent's prompt is checked against existing decisions. If a matching decision exists, its context is returned. If ambiguity is detected, clarification is requested.
2. **Enforce**: The resolved context (or new decision) is evaluated against enforcement rules. The verdict determines whether the agent can proceed.
3. **Commit**: Once approved, the decision is persisted with full audit trail — options, rationale, scope, and lifecycle state.
