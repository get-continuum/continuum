"""Postgres-backed storage backend for the hosted Continuum API.

Uses ``psycopg`` (v3, sync) with connection pooling.  The enforcement and
resolve engines still run locally via the SDK — only *storage* goes through
Postgres (Neon).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row

from continuum.enforce.engine import EnforcementEngine
from continuum.enforce.types import Action, ActionType, EnforcementResult
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


class PostgresStorageBackend:
    """Implements :class:`StorageBackend` against a Postgres (Neon) database."""

    def __init__(self, database_url: str, workspace_id: str = "ws_default") -> None:
        self._database_url = database_url
        self._workspace_id = workspace_id

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _conn(self) -> psycopg.Connection:
        return psycopg.connect(self._database_url, row_factory=dict_row)

    def _decision_from_row(self, row: dict[str, Any]) -> dict[str, Any]:
        """Convert a DB row into a dict matching the SDK Decision shape."""
        payload = row.get("payload_json") or {}
        if isinstance(payload, str):
            payload = json.loads(payload)

        enforcement: dict[str, Any] = {
            "scope": row.get("scope"),
            "decision_type": row.get("decision_type"),
            "supersedes": row.get("supersedes"),
            "precedence": row.get("precedence"),
            "override_policy": row.get("override_policy", "invalid_by_default"),
        }

        created_at = row.get("created_at")
        updated_at = row.get("updated_at")
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()
        if isinstance(updated_at, datetime):
            updated_at = updated_at.isoformat()

        return {
            "id": row["id"],
            "title": row["title"],
            "version": row.get("version", 0),
            "status": row.get("status", "draft"),
            "rationale": row.get("rationale"),
            "options_considered": payload.get("options_considered", []),
            "enforcement": enforcement,
            "stakeholders": payload.get("stakeholders", []),
            "metadata": payload.get("metadata", {}),
            "created_at": created_at,
            "updated_at": updated_at,
        }

    def _build_decision_model(
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
    ) -> tuple[str, dict[str, Any]]:
        """Build a decision ID and payload dict for insertion."""
        decision_id = f"dec_{uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)

        parsed_options: list[dict[str, Any]] = []
        if options:
            for o in options:
                if "id" not in o or not o["id"]:
                    o = {**o, "id": f"opt_{uuid4().hex[:10]}"}
                parsed_options.append(o)

        payload = {
            "options_considered": parsed_options,
            "stakeholders": stakeholders or [],
            "metadata": metadata or {},
        }

        row_data = {
            "id": decision_id,
            "workspace_id": self._workspace_id,
            "title": title,
            "rationale": rationale,
            "scope": scope,
            "decision_type": decision_type,
            "supersedes": supersedes,
            "precedence": precedence,
            "override_policy": override_policy or "invalid_by_default",
            "payload_json": json.dumps(payload),
            "created_at": now,
            "updated_at": now,
        }
        return decision_id, row_data

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
    ) -> dict[str, Any]:
        decision_id, row_data = self._build_decision_model(
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
        )
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO decisions
                    (id, workspace_id, title, rationale, scope, decision_type,
                     supersedes, precedence, override_policy, payload_json,
                     created_at, updated_at)
                VALUES
                    (%(id)s, %(workspace_id)s, %(title)s, %(rationale)s, %(scope)s,
                     %(decision_type)s, %(supersedes)s, %(precedence)s,
                     %(override_policy)s, %(payload_json)s,
                     %(created_at)s, %(updated_at)s)
                """,
                row_data,
            )
            row = conn.execute(
                "SELECT * FROM decisions WHERE id = %(id)s",
                {"id": decision_id},
            ).fetchone()
        return self._decision_from_row(row)  # type: ignore[arg-type]

    def get(self, decision_id: str) -> dict[str, Any]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM decisions WHERE id = %(id)s AND workspace_id = %(ws)s",
                {"id": decision_id, "ws": self._workspace_id},
            ).fetchone()
        if row is None:
            from continuum.exceptions import DecisionNotFoundError

            raise DecisionNotFoundError(f"Decision '{decision_id}' not found")
        return self._decision_from_row(row)

    def list_decisions(self, scope: Optional[str] = None) -> list[dict[str, Any]]:
        with self._conn() as conn:
            if scope is not None:
                rows = conn.execute(
                    """SELECT * FROM decisions
                       WHERE workspace_id = %(ws)s
                       ORDER BY created_at""",
                    {"ws": self._workspace_id},
                ).fetchall()
                # Use SDK scope matching for consistency
                return [
                    self._decision_from_row(r)
                    for r in rows
                    if scope_matches(scope, r.get("scope"))
                ]
            else:
                rows = conn.execute(
                    """SELECT * FROM decisions
                       WHERE workspace_id = %(ws)s
                       ORDER BY created_at""",
                    {"ws": self._workspace_id},
                ).fetchall()
                return [self._decision_from_row(r) for r in rows]

    def update_status(self, decision_id: str, new_status: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        with self._conn() as conn:
            conn.execute(
                """UPDATE decisions
                   SET status = %(status)s, updated_at = %(now)s
                   WHERE id = %(id)s AND workspace_id = %(ws)s""",
                {
                    "status": new_status,
                    "now": now,
                    "id": decision_id,
                    "ws": self._workspace_id,
                },
            )
            row = conn.execute(
                "SELECT * FROM decisions WHERE id = %(id)s",
                {"id": decision_id},
            ).fetchone()
        if row is None:
            from continuum.exceptions import DecisionNotFoundError

            raise DecisionNotFoundError(f"Decision '{decision_id}' not found")
        return self._decision_from_row(row)

    def inspect(self, scope: str) -> list[dict[str, Any]]:
        all_decisions = self.list_decisions()
        return [
            d
            for d in all_decisions
            if d.get("status") == "active"
            and d.get("enforcement") is not None
            and scope_matches(d["enforcement"].get("scope", ""), scope)
        ]

    def enforce(self, action: dict[str, Any], scope: str) -> dict[str, Any]:
        # Fetch decisions, reconstruct SDK Decision models, run engine
        rows = self.list_decisions()
        decisions = [Decision.model_validate(r) for r in rows]
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
        candidates: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        rows = self.list_decisions()
        enriched_candidates = list(candidates or [])
        candidate_objs = [
            CandidateOption(id=c["id"], title=c["title"]) for c in enriched_candidates
        ]
        result: ResolveResult = _resolve_fn(
            query=query,
            scope=scope,
            candidates=candidate_objs,
            decisions=rows,
        )
        return result.model_dump(mode="json")

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
    ) -> dict[str, Any]:
        old = self.get(old_id)

        # Mark old as superseded
        self.update_status(old_id, "superseded")

        # Derive scope and type from old decision
        enforcement = old.get("enforcement") or {}
        scope = enforcement.get("scope", "")
        decision_type = enforcement.get("decision_type", "interpretation")

        # Commit new decision
        new_dec = self.commit(
            title=new_title,
            scope=scope,
            decision_type=decision_type,
            rationale=rationale,
            options=options,
            stakeholders=stakeholders,
            metadata=metadata,
            override_policy=override_policy,
            precedence=precedence,
            supersedes=old_id,
        )

        # Activate immediately
        activated = self.update_status(new_dec["id"], "active")
        return activated
