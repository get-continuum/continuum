"""Deterministic lifecycle state machine for decisions."""

from __future__ import annotations

from datetime import datetime, timezone

from continuum.exceptions import TransitionError
from continuum.models import Decision, DecisionStatus

VALID_TRANSITIONS: dict[DecisionStatus, list[DecisionStatus]] = {
    DecisionStatus.draft: [DecisionStatus.active, DecisionStatus.archived],
    DecisionStatus.active: [DecisionStatus.superseded, DecisionStatus.archived],
    DecisionStatus.superseded: [DecisionStatus.archived],
    DecisionStatus.archived: [],
}


def can_transition(current: DecisionStatus, target: DecisionStatus) -> bool:
    """Return True if *current* -> *target* is a valid lifecycle transition."""
    return target in VALID_TRANSITIONS.get(current, [])


def transition(decision: Decision, new_status: DecisionStatus) -> Decision:
    """Return a new Decision with *new_status* applied.

    Raises
    ------
    TransitionError
        If the transition from the current status to *new_status* is not allowed.
    """
    current = DecisionStatus(decision.status)
    target = DecisionStatus(new_status)

    if not can_transition(current, target):
        raise TransitionError(
            f"Cannot transition from '{current.value}' to '{target.value}'"
        )

    return decision.model_copy(
        update={
            "status": target,
            "updated_at": datetime.now(timezone.utc),
        }
    )
