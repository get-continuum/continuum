"""LlamaIndex ToolSpec-style wrapper for Continuum.

This module intentionally keeps a minimal surface area:
- It does not require LlamaIndex at import time.
- It exposes callables that can be wrapped as tools in LlamaIndex (or any agent runtime).
"""

from __future__ import annotations

from typing import Any

from continuum.client import ContinuumClient


class ContinuumToolSpec:
    """Expose Continuum operations as simple functions.

    Parameters
    ----------
    storage_dir:
        Optional path to repo-local `.continuum/` directory.
    """

    # LlamaIndex convention: these names are exposed as tools.
    spec_functions = ["inspect", "resolve", "enforce", "commit", "supersede"]

    def __init__(self, storage_dir: str | None = None) -> None:
        self._client = ContinuumClient(storage_dir=storage_dir) if storage_dir else ContinuumClient()

    def inspect(self, scope: str) -> list[dict[str, Any]]:
        """Return the active binding set for a scope."""
        return self._client.inspect(scope)

    def resolve(
        self,
        prompt: str,
        scope: str,
        candidates: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Resolve a prompt against prior decisions (ambiguity gate)."""
        return self._client.resolve(query=prompt, scope=scope, candidates=candidates)

    def enforce(self, action: dict[str, Any], scope: str) -> dict[str, Any]:
        """Evaluate enforcement rules for a proposed action in a scope."""
        return self._client.enforce(action=action, scope=scope)

    def commit(
        self,
        title: str,
        scope: str,
        decision_type: str,
        rationale: str,
        options: list[dict[str, Any]] | None = None,
        stakeholders: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        override_policy: str | None = None,
        precedence: int | None = None,
        supersedes: str | None = None,
        activate: bool = False,
    ) -> dict[str, Any]:
        """Persist a new decision (optionally activate)."""
        dec = self._client.commit(
            title=title,
            scope=scope,
            decision_type=decision_type,
            rationale=rationale,
            options=options,
            stakeholders=stakeholders,
            metadata=metadata,
            override_policy=override_policy,
            precedence=precedence,
            supersedes=supersedes,
        )
        if activate:
            dec = self._client.update_status(dec.id, "active")
        return dec.model_dump(mode="json")

    def supersede(
        self,
        old_id: str,
        new_title: str,
        rationale: str | None = None,
        options: list[dict[str, Any]] | None = None,
        stakeholders: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        override_policy: str | None = None,
        precedence: int | None = None,
    ) -> dict[str, Any]:
        """Supersede an existing decision and activate the replacement."""
        dec = self._client.supersede(
            old_id=old_id,
            new_title=new_title,
            rationale=rationale,
            options=options,
            stakeholders=stakeholders,
            metadata=metadata,
            override_policy=override_policy,
            precedence=precedence,
        )
        return dec.model_dump(mode="json")

