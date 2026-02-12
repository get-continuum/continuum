"""StorageBackend protocol for the Continuum API.

Defines the interface that both the local (file-based) and hosted (Postgres)
backends must implement.  Routes are agnostic to the concrete backend.
"""

from __future__ import annotations

from typing import Any, Optional, Protocol, runtime_checkable


@runtime_checkable
class StorageBackend(Protocol):
    """Abstract storage interface consumed by the API routes."""

    def commit(
        self,
        title: str,
        scope: str,
        decision_type: str,
        options: Optional[list[dict[str, Any]]] = None,
        rationale: Optional[str] = None,
        stakeholders: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        override_policy: Optional[str] = None,
        precedence: Optional[int] = None,
        supersedes: Optional[str] = None,
        key: Optional[str] = None,
    ) -> dict[str, Any]:
        """Create and persist a new decision.  Returns the decision as a dict."""
        ...

    def get(self, decision_id: str) -> dict[str, Any]:
        """Load a single decision by its ID."""
        ...

    def list_decisions(self, scope: Optional[str] = None) -> list[dict[str, Any]]:
        """Return all persisted decisions, optionally filtered by scope."""
        ...

    def update_status(self, decision_id: str, new_status: str) -> dict[str, Any]:
        """Transition a decision to a new lifecycle status."""
        ...

    def inspect(self, scope: str) -> dict[str, Any]:
        """Return the effective binding set for *scope*.

        Returns a dict with ``bindings``, ``conflict_notes``, and ``items``
        (legacy flat list equal to ``bindings``).
        """
        ...

    def enforce(self, action: dict[str, Any], scope: str) -> dict[str, Any]:
        """Evaluate an action against active decisions in *scope*."""
        ...

    def resolve(
        self,
        query: str,
        scope: str,
        candidates: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        """Run the ambiguity gate for *query* against decisions in *scope*."""
        ...

    def supersede(
        self,
        old_id: str,
        new_title: str,
        rationale: Optional[str] = None,
        options: Optional[list[dict[str, Any]]] = None,
        stakeholders: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        override_policy: Optional[str] = None,
        precedence: Optional[int] = None,
        key: Optional[str] = None,
    ) -> dict[str, Any]:
        """Supersede an existing decision and commit a replacement."""
        ...
