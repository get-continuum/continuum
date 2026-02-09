"""LangGraph node implementations for Continuum.

These nodes are intentionally lightweight: they operate on a plain `dict` state and
call the stable Continuum SDK convenience methods.

Expected state keys (conventions, customize as needed):
  - storage_dir: optional path to repo-local `.continuum/` directory
  - scope: required scope string

Resolve:
  - prompt (or query): required
  - candidates: optional list[{"id": "...", "title": "..."}]
  - output: resolution (dict)

Enforce:
  - action: required dict (type, description, metadata)
  - output: enforcement_result (dict)

Commit:
  - title, scope, decision_type, rationale: required
  - options, stakeholders, metadata, override_policy, precedence, supersedes, activate: optional
  - output: committed_decision (dict)
"""

from __future__ import annotations

from typing import Any

from continuum.client import ContinuumClient


def _client_from_state(state: dict[str, Any]) -> ContinuumClient:
    storage_dir = state.get("storage_dir")
    return ContinuumClient(storage_dir=storage_dir) if storage_dir else ContinuumClient()


def resolve_node(state: dict[str, Any]) -> dict[str, Any]:
    """Resolve node: check if a prior decision covers the current prompt."""
    client = _client_from_state(state)
    scope = str(state["scope"])
    prompt = str(state.get("prompt") or state.get("query") or "")
    candidates = state.get("candidates")

    resolution = client.resolve(query=prompt, scope=scope, candidates=candidates)
    return {**state, "resolution": resolution}


def enforce_node(state: dict[str, Any]) -> dict[str, Any]:
    """Enforce node: evaluate enforcement rules for the proposed action."""
    client = _client_from_state(state)
    scope = str(state["scope"])
    action = state.get("action") or {}

    enforcement_result = client.enforce(action=action, scope=scope)
    return {**state, "enforcement_result": enforcement_result}


def commit_node(state: dict[str, Any]) -> dict[str, Any]:
    """Commit node: persist a decision (optionally activate)."""
    client = _client_from_state(state)

    dec = client.commit(
        title=str(state["title"]),
        scope=str(state["scope"]),
        decision_type=str(state["decision_type"]),
        rationale=state.get("rationale"),
        options=state.get("options"),
        stakeholders=state.get("stakeholders"),
        metadata=state.get("metadata"),
        override_policy=state.get("override_policy"),
        precedence=state.get("precedence"),
        supersedes=state.get("supersedes"),
    )
    if state.get("activate"):
        dec = client.update_status(dec.id, "active")

    return {**state, "committed_decision": dec.model_dump(mode="json")}

