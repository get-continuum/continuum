"""Tests for Continuum Pydantic models."""

from __future__ import annotations

from datetime import datetime, timezone

from continuum.models import (
    Decision,
    DecisionContext,
    DecisionStatus,
    DecisionType,
    Enforcement,
    Option,
    OverridePolicy,
)


def test_decision_creation() -> None:
    """Create a Decision with all fields populated."""
    now = datetime.now(timezone.utc)
    decision = Decision(
        id="dec_abc123",
        version=1,
        status=DecisionStatus.active,
        title="Use UTC everywhere",
        rationale="Consistency across services",
        options_considered=[
            Option(id="opt_1", title="UTC", selected=True),
            Option(id="opt_2", title="Local TZ", selected=False, rejected_reason="Ambiguous"),
        ],
        context=DecisionContext(
            trigger="timezone bug",
            source="incident-42",
            timestamp=now,
            actor="alice",
        ),
        enforcement=Enforcement(
            scope="backend",
            decision_type=DecisionType.preference,
            override_policy=OverridePolicy.warn,
        ),
        stakeholders=["alice", "bob"],
        metadata={"team": "platform"},
        created_at=now,
        updated_at=now,
    )

    assert decision.id == "dec_abc123"
    assert decision.status == "active"
    assert decision.version == 1
    assert len(decision.options_considered) == 2
    assert decision.enforcement is not None
    assert decision.enforcement["scope"] == "backend"
    assert decision.context is not None


def test_option_model() -> None:
    """Create an Option and verify fields."""
    opt = Option(id="opt_x", title="Do nothing", selected=False, rejected_reason="Risky")
    assert opt.id == "opt_x"
    assert opt.selected is False
    assert opt.rejected_reason == "Risky"


def test_decision_status_enum() -> None:
    """Verify all expected enum values exist."""
    assert DecisionStatus.draft.value == "draft"
    assert DecisionStatus.active.value == "active"
    assert DecisionStatus.superseded.value == "superseded"
    assert DecisionStatus.archived.value == "archived"


def test_decision_serialization() -> None:
    """Round-trip a Decision through model_dump / model_validate."""
    now = datetime.now(timezone.utc)
    original = Decision(
        id="dec_rt001",
        title="Serialization test",
        created_at=now,
        updated_at=now,
    )

    data = original.model_dump()
    restored = Decision.model_validate(data)

    assert restored.id == original.id
    assert restored.title == original.title
    assert restored.status == "draft"
    assert restored.version == 0
