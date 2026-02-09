#!/usr/bin/env python3
"""Working LangGraph example using Continuum.

Run (after installing deps):
  pip install continuum-sdk continuum-langgraph langgraph
  python oss/integrations/langgraph/examples/working_example.py
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypedDict

from langgraph.graph import StateGraph

from continuum import ContinuumClient
from continuum_langgraph import commit_node, enforce_node, resolve_node


class AgentState(TypedDict, total=False):
    storage_dir: str
    scope: str
    prompt: str
    candidates: list[dict[str, Any]]
    action: dict[str, Any]
    resolution: dict[str, Any]
    enforcement_result: dict[str, Any]
    title: str
    decision_type: str
    rationale: str
    metadata: dict[str, Any]
    activate: bool
    committed_decision: dict[str, Any]


def main() -> None:
    # Use a local demo store.
    storage_dir = ".continuum-demo"
    scope = "repo:langgraph-demo"

    # Seed a decision so resolve/enforce have something to do.
    client = ContinuumClient(storage_dir=storage_dir)
    dec = client.commit(
        title="Reject full rewrites",
        scope=scope,
        decision_type="rejection",
        options=[
            {"title": "Incremental refactor", "selected": True},
            {"title": "Full rewrite", "selected": False, "rejected_reason": "Too risky"},
        ],
        rationale="Prefer incremental refactors.",
    )
    client.update_status(dec.id, "active")

    graph = StateGraph(AgentState)
    graph.add_node("resolve", resolve_node)
    graph.add_node("enforce", enforce_node)
    graph.add_node("commit", commit_node)

    graph.add_edge("resolve", "enforce")
    graph.add_edge("enforce", "commit")
    graph.set_entry_point("resolve")
    app = graph.compile()

    initial: AgentState = {
        "storage_dir": storage_dir,
        "scope": scope,
        "prompt": "Reject full rewrites",
        "action": {"type": "code_change", "description": "Do a full rewrite of auth module"},
        # Commit a new interpretation decision at the end (just to show commit_node).
        "title": "production-ready",
        "decision_type": "interpretation",
        "rationale": "Production-ready means tests + error handling.",
        "metadata": {"selected_option_id": "opt_tests_errors"},
        "activate": True,
    }

    final = app.invoke(initial)
    print("resolution:", final.get("resolution"))
    print("enforcement_result:", final.get("enforcement_result"))
    print("committed_decision:", final.get("committed_decision"))


if __name__ == "__main__":
    main()

