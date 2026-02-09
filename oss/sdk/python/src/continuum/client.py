"""High-level client for creating, storing, and querying decisions."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from continuum.enforce.engine import EnforcementEngine
from continuum.enforce.types import Action, ActionType, EnforcementResult
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
from continuum.resolve.resolve import resolve as _resolve_fn
from continuum.resolve.types import CandidateOption, ResolveResult
from continuum.scope import scope_matches


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
        override_policy: str | None = None,
        precedence: int | None = None,
        supersedes: str | None = None,
    ) -> Decision:
        """Create and persist a new decision.

        Returns the newly created :class:`Decision`.
        """
        now = datetime.now(timezone.utc)
        decision_id = f"dec_{uuid4().hex[:12]}"

        parsed_options: list[Option] = []
        if options:
            for o in options:
                # Keep docs/examples ergonomic while persisting spec-compliant records.
                if "id" not in o or not o["id"]:
                    o = {**o, "id": f"opt_{uuid4().hex[:10]}"}
                parsed_options.append(Option(**o))

        enforcement = Enforcement(
            scope=scope,
            decision_type=DecisionType(decision_type),
            supersedes=supersedes,
            precedence=precedence,
            override_policy=OverridePolicy(override_policy)
            if override_policy
            else OverridePolicy.invalid_by_default,
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
                    # Filter supports wildcard and prefix matching.
                    if scope_matches(scope, enforcement_scope):
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
    # Convenience methods
    # ------------------------------------------------------------------

    def inspect(self, scope: str) -> list[dict]:
        """Return all active decisions for *scope* as plain dicts.

        This is the "binding set" — the decisions currently in effect.
        """
        # Binding set includes decisions whose scope applies to the target scope.
        decisions = self.list_decisions()
        return [
            d.model_dump(mode="json")
            for d in decisions
            if d.status in ("active", DecisionStatus.active)
            and d.enforcement is not None
            and scope_matches(
                (
                    d.enforcement.get("scope")
                    if isinstance(d.enforcement, dict)
                    else d.enforcement.scope
                ),
                scope,
            )
        ]

    def enforce(self, action: dict, scope: str) -> dict:
        """Evaluate an *action* dict against active decisions in *scope*.

        Parameters
        ----------
        action:
            Dict with ``type`` (ActionType value) and ``description`` keys.
        scope:
            The enforcement scope to check against.

        Returns
        -------
        dict
            Enforcement result with ``verdict``, ``reason``, etc.
        """
        decisions = self.list_decisions()
        engine = EnforcementEngine(decisions)
        action_obj = Action(
            type=ActionType(action.get("type", "generic")),
            description=action.get("description", action.get("summary", "")),
            scope=scope,
            metadata=action.get("metadata", {}),
        )
        result: EnforcementResult = engine.evaluate(action_obj)
        return result.model_dump(mode="json")

    def resolve(
        self,
        query: str,
        scope: str,
        candidates: list[dict] | None = None,
    ) -> dict:
        """Run the ambiguity gate for *query* against decisions in *scope*.

        Parameters
        ----------
        query:
            Free-text query describing the intent.
        scope:
            Enforcement scope.
        candidates:
            Optional list of candidate option dicts (``id``, ``title``).

        Returns
        -------
        dict
            Resolve result with ``status`` ("resolved" | "needs_clarification").
        """
        decisions = self.list_decisions()
        decision_dicts = [d.model_dump(mode="json") for d in decisions]
        candidate_objs = [
            CandidateOption(id=c["id"], title=c["title"])
            for c in (candidates or [])
        ]
        result: ResolveResult = _resolve_fn(
            query=query,
            scope=scope,
            candidates=candidate_objs,
            decisions=decision_dicts,
        )
        return result.model_dump(mode="json")

    def supersede(self, old_id: str, new_title: str, **kwargs: object) -> Decision:
        """Supersede an existing decision and commit a replacement.

        Transitions the old decision to ``superseded`` and creates a new
        decision that records the supersession.

        Parameters
        ----------
        old_id:
            ID of the decision being replaced.
        new_title:
            Title for the replacement decision.
        **kwargs:
            Additional keyword arguments forwarded to :meth:`commit`.

        Returns
        -------
        Decision
            The newly committed replacement decision.
        """
        old_decision = self._load(old_id)

        # Transition old decision to superseded
        updated_old = transition(old_decision, DecisionStatus.superseded)
        self._save(updated_old)

        # Determine scope from old decision
        scope = kwargs.pop("scope", None)  # type: ignore[arg-type]
        if scope is None and old_decision.enforcement is not None:
            scope = (
                old_decision.enforcement.get("scope")
                if isinstance(old_decision.enforcement, dict)
                else old_decision.enforcement.scope
            )

        # Determine decision_type from old decision
        decision_type = kwargs.pop("decision_type", None)  # type: ignore[arg-type]
        if decision_type is None and old_decision.enforcement is not None:
            decision_type = (
                old_decision.enforcement.get("decision_type")
                if isinstance(old_decision.enforcement, dict)
                else old_decision.enforcement.decision_type
            )

        new_dec = self.commit(
            title=new_title,
            scope=scope,  # type: ignore[arg-type]
            decision_type=decision_type,  # type: ignore[arg-type]
            supersedes=old_id,
            **kwargs,  # type: ignore[arg-type]
        )

        # Activate the new decision immediately
        activated = transition(new_dec, DecisionStatus.active)
        self._save(activated)

        return activated

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
