"""File-based storage backend wrapping the Continuum SDK ContinuumClient.

This is the default backend used when ``CONTINUUM_MODE=local`` (or unset).
Behaviour is identical to the original demo API — no database required.
"""

from __future__ import annotations

from typing import Any, Optional

from continuum.client import ContinuumClient


class FileStorageBackend:
    """Thin wrapper around :class:`ContinuumClient` implementing the
    :class:`StorageBackend` protocol."""

    def __init__(self, storage_dir: str) -> None:
        self._client = ContinuumClient(storage_dir=storage_dir)

    # ------------------------------------------------------------------
    # StorageBackend interface
    # ------------------------------------------------------------------

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
        dec = self._client.commit(
            title=title,
            scope=scope,
            decision_type=decision_type,
            options=options,
            rationale=rationale,
            stakeholders=stakeholders,
            metadata=metadata,
            override_policy=override_policy,
            precedence=precedence,
            supersedes=supersedes,
            key=key,
        )
        return dec.model_dump(mode="json")

    def get(self, decision_id: str) -> dict[str, Any]:
        return self._client.get(decision_id).model_dump(mode="json")

    def list_decisions(self, scope: Optional[str] = None) -> list[dict[str, Any]]:
        return [
            d.model_dump(mode="json") for d in self._client.list_decisions(scope=scope)
        ]

    def update_status(self, decision_id: str, new_status: str) -> dict[str, Any]:
        return self._client.update_status(decision_id, new_status).model_dump(
            mode="json"
        )

    def inspect(self, scope: str) -> dict[str, Any]:
        return self._client.inspect(scope)

    def enforce(self, action: dict[str, Any], scope: str) -> dict[str, Any]:
        return self._client.enforce(action=action, scope=scope)

    def resolve(
        self,
        query: str,
        scope: str,
        candidates: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        return self._client.resolve(query=query, scope=scope, candidates=candidates)

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
        dec = self._client.supersede(
            old_id=old_id,
            new_title=new_title,
            rationale=rationale,
            options=options,
            stakeholders=stakeholders,
            metadata=metadata,
            override_policy=override_policy,
            precedence=precedence,
            key=key,
        )
        return dec.model_dump(mode="json")
