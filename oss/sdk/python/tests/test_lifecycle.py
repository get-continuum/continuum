"""Tests for the Continuum lifecycle state machine."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from continuum.exceptions import TransitionError
from continuum.lifecycle import can_transition, transition
from continuum.models import Decision, DecisionStatus


def _make_decision(status: DecisionStatus = DecisionStatus.draft) -> Decision:
    now = datetime.now(timezone.utc)
    return Decision(
        id="dec_lifecycle01",
        status=status,
        title="Lifecycle test",
        created_at=now,
        updated_at=now,
    )


def test_valid_transitions() -> None:
    """Allowed transitions produce the expected new status."""
    # draft -> active
    d1 = transition(_make_decision(DecisionStatus.draft), DecisionStatus.active)
    assert d1.status == "active"

    # active -> superseded
    d2 = transition(_make_decision(DecisionStatus.active), DecisionStatus.superseded)
    assert d2.status == "superseded"

    # active -> archived
    d3 = transition(_make_decision(DecisionStatus.active), DecisionStatus.archived)
    assert d3.status == "archived"

    # draft -> archived
    d4 = transition(_make_decision(DecisionStatus.draft), DecisionStatus.archived)
    assert d4.status == "archived"

    # superseded -> archived
    d5 = transition(_make_decision(DecisionStatus.superseded), DecisionStatus.archived)
    assert d5.status == "archived"


def test_invalid_transition_raises() -> None:
    """Disallowed transitions raise TransitionError."""
    with pytest.raises(TransitionError):
        transition(_make_decision(DecisionStatus.active), DecisionStatus.draft)


def test_archived_is_terminal() -> None:
    """Archived decisions cannot transition to any other status."""
    archived = _make_decision(DecisionStatus.archived)
    for target in (DecisionStatus.draft, DecisionStatus.active, DecisionStatus.superseded):
        with pytest.raises(TransitionError):
            transition(archived, target)


def test_can_transition() -> None:
    """Boolean helper returns correct results."""
    assert can_transition(DecisionStatus.draft, DecisionStatus.active) is True
    assert can_transition(DecisionStatus.active, DecisionStatus.draft) is False
    assert can_transition(DecisionStatus.archived, DecisionStatus.active) is False
    assert can_transition(DecisionStatus.superseded, DecisionStatus.archived) is True
