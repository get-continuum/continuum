"""High-level client for creating, storing, and querying decisions."""

from __future__ import annotations

import hashlib
import json as _json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from continuum.enforce.engine import EnforcementEngine
from continuum.enforce.types import Action, ActionType, EnforcementResult
from continuum.exceptions import DecisionNotFoundError
from continuum.lifecycle import transition
from continuum.memory import MemorySignalSource
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


def compute_value_hash(
    binding_key: str,
    decision_type: str,
    title: str,
    rationale: str | None,
    selected_option_ids: list[str] | None = None,
) -> str:
    """Return a stable fingerprint of a decision's effective value.

    Used for idempotency checks: two decisions with the same hash are
    considered identical in value.
    """
    parts = {
        "binding_key": binding_key,
        "decision_type": decision_type,
        "title": title,
        "rationale": rationale or "",
        "selected_options": sorted(selected_option_ids or []),
    }
    blob = _json.dumps(parts, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


class ContinuumClient:
    """File-backed client for the Continuum decision framework.

    Parameters
    ----------
    storage_dir:
        Root directory for persisted decisions.  Defaults to ``.continuum/``
        in the current working directory.
    memory_source:
        Optional :class:`MemorySignalSource` implementation.  When provided,
        :meth:`resolve` enriches candidates with memory signals.
    """

    def __init__(
        self,
        storage_dir: str | Path | None = None,
        memory_source: MemorySignalSource | None = None,
    ) -> None:
        self._storage_dir = Path(storage_dir) if storage_dir else Path(".continuum")
        self._decisions_dir = self._storage_dir / "decisions"
        self._decisions_dir.mkdir(parents=True, exist_ok=True)
        self._memory_source = memory_source

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
        key: str | None = None,
    ) -> Decision:
        """Create and persist a new decision.

        Parameters
        ----------
        key:
            Optional semantic binding key.  When omitted, *title* is used
            as the ``binding_key``.

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

        bk = key or title
        selected_ids = [
            o.id for o in parsed_options if o.selected
        ]
        vh = compute_value_hash(
            binding_key=bk,
            decision_type=decision_type,
            title=title,
            rationale=rationale,
            selected_option_ids=selected_ids or None,
        )

        enforcement = Enforcement(
            scope=scope,
            key=key,
            binding_key=bk,
            value_hash=vh,
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

        When activating (``new_status='active'``), the auto-supersede gate
        enforces one active decision per ``(scope, binding_key)``:

        * **Idempotent**: if an active decision with the same ``binding_key``
          and ``value_hash`` already exists, the draft is deleted and the
          existing active is returned.
        * **Auto-supersede**: if an active decision with the same
          ``binding_key`` but a *different* ``value_hash`` exists, it is
          transitioned to ``superseded`` before the new one is activated.

        Returns the updated :class:`Decision`.
        """
        decision = self._load(decision_id)
        target = DecisionStatus(new_status)

        if target == DecisionStatus.active:
            bk = self._get_binding_key(decision)
            scope = self._get_enforcement_scope(decision)
            if bk and scope:
                vh = self._get_value_hash(decision)
                existing = self._find_active_for_binding_key(scope, bk)
                for ex in existing:
                    if ex.id == decision_id:
                        continue
                    if self._get_value_hash(ex) == vh:
                        # Idempotent: exact same value → delete draft, return existing
                        self._delete(decision.id)
                        return ex
                    # Different value → supersede the old one
                    self._save(transition(ex, DecisionStatus.superseded))

        updated = transition(decision, target)
        self._save(updated)
        return updated

    # ------------------------------------------------------------------
    # Convenience methods
    # ------------------------------------------------------------------

    def inspect(self, scope: str) -> dict:
        """Return the effective binding set for *scope*.

        Returns a dict with:

        * ``bindings`` — one winner per ``binding_key`` (highest precedence,
          then newest ``created_at``).
        * ``conflict_notes`` — entries for any duplicate actives that were
          outranked.
        * ``items`` — legacy flat list equal to ``bindings`` for backward
          compatibility.
        """
        decisions = self.list_decisions()
        actives = [
            d
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

        # Group by binding_key
        by_key: dict[str, list[dict]] = {}
        for d in actives:
            bk = self._get_binding_key(d)
            by_key.setdefault(bk, []).append(d.model_dump(mode="json"))

        bindings: list[dict] = []
        conflict_notes: list[dict] = []
        for bk, decs in by_key.items():
            # Winner: highest precedence, then newest created_at
            winner = max(
                decs,
                key=lambda d: (
                    (d.get("enforcement") or {}).get("precedence") or 0,
                    d.get("created_at", ""),
                ),
            )
            bindings.append(winner)
            for d in decs:
                if d["id"] != winner["id"]:
                    conflict_notes.append({
                        "binding_key": bk,
                        "decision_id": d["id"],
                        "winner_id": winner["id"],
                        "note": (
                            f"Duplicate active for binding_key '{bk}'; "
                            f"superseded by {winner['id']}"
                        ),
                    })

        return {
            "bindings": bindings,
            "conflict_notes": conflict_notes,
            "items": bindings,
        }

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

        If a ``memory_source`` was provided at construction time, memory signals
        are searched and appended to the candidate list before resolution.

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

        enriched_candidates = list(candidates or [])

        # Enrich candidates from memory signals when a source is available.
        if self._memory_source is not None:
            signals = self._memory_source.search(query, scope=scope, limit=5)
            for sig in signals:
                enriched_candidates.append({
                    "id": sig.get("id", ""),
                    "title": sig.get("content", ""),
                })

        candidate_objs = [
            CandidateOption(id=c["id"], title=c["title"])
            for c in enriched_candidates
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
        decision that records the supersession.  The new decision is activated
        via :meth:`update_status` so that the auto-supersede gate is applied.

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

        # Inherit key from old decision if not provided
        key = kwargs.pop("key", None)  # type: ignore[arg-type]
        if key is None and old_decision.enforcement is not None:
            key = (
                old_decision.enforcement.get("key")
                if isinstance(old_decision.enforcement, dict)
                else old_decision.enforcement.key
            )

        new_dec = self.commit(
            title=new_title,
            scope=scope,  # type: ignore[arg-type]
            decision_type=decision_type,  # type: ignore[arg-type]
            supersedes=old_id,
            key=key,  # type: ignore[arg-type]
            **kwargs,  # type: ignore[arg-type]
        )

        # Activate via update_status so the auto-supersede gate runs
        return self.update_status(new_dec.id, "active")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_binding_key(decision: Decision) -> str:
        """Return the effective binding key for *decision*.

        Priority: ``enforcement.binding_key`` > ``enforcement.key`` > ``title``.
        """
        if decision.enforcement is not None:
            enf = decision.enforcement
            if isinstance(enf, dict):
                return enf.get("binding_key") or enf.get("key") or decision.title
            return enf.binding_key or enf.key or decision.title
        return decision.title

    @staticmethod
    def _get_enforcement_scope(decision: Decision) -> str | None:
        """Extract enforcement scope from *decision*."""
        if decision.enforcement is None:
            return None
        enf = decision.enforcement
        if isinstance(enf, dict):
            return enf.get("scope")
        return enf.scope

    @staticmethod
    def _get_value_hash(decision: Decision) -> str:
        """Return the stored value hash, or recompute it for legacy records."""
        if decision.enforcement is not None:
            enf = decision.enforcement
            vh = enf.get("value_hash") if isinstance(enf, dict) else enf.value_hash
            if vh:
                return vh
        # Recompute for records that pre-date value_hash
        bk = ContinuumClient._get_binding_key(decision)
        dt = ""
        if decision.enforcement is not None:
            enf = decision.enforcement
            dt = (
                enf.get("decision_type", "")
                if isinstance(enf, dict)
                else (enf.decision_type or "")
            )
        selected_ids = [
            o.id
            for o in (decision.options_considered or [])
            if isinstance(o, Option) and o.selected
        ]
        return compute_value_hash(
            binding_key=bk,
            decision_type=str(dt),
            title=decision.title,
            rationale=decision.rationale,
            selected_option_ids=selected_ids or None,
        )

    def _find_active_for_binding_key(
        self, scope: str, binding_key: str
    ) -> list[Decision]:
        """Return all active decisions with exact *scope* and *binding_key*."""
        results: list[Decision] = []
        for dec in self.list_decisions():
            if dec.status not in ("active", DecisionStatus.active):
                continue
            if dec.enforcement is None:
                continue
            dec_scope = self._get_enforcement_scope(dec)
            if dec_scope != scope:
                continue
            if self._get_binding_key(dec) == binding_key:
                results.append(dec)
        return results

    def _save(self, decision: Decision) -> None:
        path = self._decisions_dir / f"{decision.id}.json"
        path.write_text(decision.model_dump_json(indent=2))

    def _load(self, decision_id: str) -> Decision:
        path = self._decisions_dir / f"{decision_id}.json"
        if not path.exists():
            raise DecisionNotFoundError(f"Decision '{decision_id}' not found")
        return Decision.model_validate_json(path.read_text())

    def _delete(self, decision_id: str) -> None:
        """Remove a persisted decision file (e.g. abandoned draft)."""
        path = self._decisions_dir / f"{decision_id}.json"
        path.unlink(missing_ok=True)
