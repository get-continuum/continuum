"""High-level client for creating, storing, and querying decisions."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from continuum.exceptions import DecisionNotFoundError
from continuum.lifecycle import transition
from continuum.models import (
    Decision,
    DecisionStatus,
    DecisionType,
    Enforcement,
    Option,
    OverridePolicy,
)


class ContinuumClient:
    """File-backed client for the Continuum decision framework.

    Parameters
    ----------
    storage_dir:
        Root directory for persisted decisions.  Defaults to ``.continuum/``
        in the current working directory.
    """

    def __init__(self, storage_dir: str | Path | None = None) -> None:
        self._storage_dir = Path(storage_dir) if storage_dir else Path(".continuum")
        self._decisions_dir = self._storage_dir / "decisions"
        self._decisions_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def commit(
        self,
        title: str,
        scope: str,
        decision_type: str,
        options: list[dict] | None = None,
        rationale: str | None = None,
        stakeholders: list[str] | None = None,
        metadata: dict | None = None,
    ) -> Decision:
        """Create and persist a new decision.

        Returns the newly created :class:`Decision`.
        """
        now = datetime.now(timezone.utc)
        decision_id = f"dec_{uuid4().hex[:12]}"

        parsed_options = [Option(**o) for o in options] if options else []

        enforcement = Enforcement(
            scope=scope,
            decision_type=DecisionType(decision_type),
            override_policy=OverridePolicy.invalid_by_default,
        )

        decision = Decision(
            id=decision_id,
            title=title,
            rationale=rationale,
            options_considered=parsed_options,
            enforcement=enforcement,
            stakeholders=stakeholders or [],
            metadata=metadata or {},
            created_at=now,
            updated_at=now,
        )

        self._save(decision)
        return decision

    def get(self, decision_id: str) -> Decision:
        """Load a single decision by its ID.

        Raises
        ------
        DecisionNotFoundError
            If no decision with *decision_id* exists.
        """
        return self._load(decision_id)

    def list_decisions(self, scope: str | None = None) -> list[Decision]:
        """Return all persisted decisions, optionally filtered by enforcement scope."""
        decisions: list[Decision] = []
        for path in sorted(self._decisions_dir.glob("*.json")):
            decision = Decision.model_validate_json(path.read_text())
            if scope is not None:
                if decision.enforcement is not None:
                    enforcement_scope = (
                        decision.enforcement.get("scope")
                        if isinstance(decision.enforcement, dict)
                        else decision.enforcement.scope
                    )
                    if enforcement_scope == scope:
                        decisions.append(decision)
            else:
                decisions.append(decision)
        return decisions

    def update_status(self, decision_id: str, new_status: str) -> Decision:
        """Transition a decision to a new lifecycle status.

        Returns the updated :class:`Decision`.
        """
        decision = self._load(decision_id)
        updated = transition(decision, DecisionStatus(new_status))
        self._save(updated)
        return updated

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _save(self, decision: Decision) -> None:
        path = self._decisions_dir / f"{decision.id}.json"
        path.write_text(decision.model_dump_json(indent=2))

    def _load(self, decision_id: str) -> Decision:
        path = self._decisions_dir / f"{decision_id}.json"
        if not path.exists():
            raise DecisionNotFoundError(f"Decision '{decision_id}' not found")
        return Decision.model_validate_json(path.read_text())
