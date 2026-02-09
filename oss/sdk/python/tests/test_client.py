"""Tests for the ContinuumClient."""

from __future__ import annotations

from pathlib import Path

import pytest

from continuum.client import ContinuumClient
from continuum.exceptions import DecisionNotFoundError


def _make_client(tmp_dir: Path) -> ContinuumClient:
    return ContinuumClient(storage_dir=tmp_dir / ".continuum")


def test_commit_and_get(tmp_dir: Path) -> None:
    """Committing a decision and retrieving it returns the same data."""
    client = _make_client(tmp_dir)
    dec = client.commit(
        title="Use Pydantic v2",
        scope="sdk",
        decision_type="preference",
        rationale="Better performance",
    )

    loaded = client.get(dec.id)
    assert loaded.id == dec.id
    assert loaded.title == "Use Pydantic v2"
    assert loaded.status == "draft"


def test_list_decisions(tmp_dir: Path) -> None:
    """Listing returns all committed decisions."""
    client = _make_client(tmp_dir)
    client.commit(title="Dec A", scope="api", decision_type="interpretation")
    client.commit(title="Dec B", scope="api", decision_type="rejection")

    decisions = client.list_decisions()
    assert len(decisions) == 2


def test_list_by_scope(tmp_dir: Path) -> None:
    """Filtering by scope returns only matching decisions."""
    client = _make_client(tmp_dir)
    client.commit(title="API rule", scope="api", decision_type="behavior_rule")
    client.commit(title="CLI rule", scope="cli", decision_type="behavior_rule")

    api_decisions = client.list_decisions(scope="api")
    assert len(api_decisions) == 1


def test_update_status(tmp_dir: Path) -> None:
    """Updating status transitions the decision lifecycle."""
    client = _make_client(tmp_dir)
    dec = client.commit(title="Promote me", scope="core", decision_type="preference")
    assert dec.status == "draft"

    updated = client.update_status(dec.id, "active")
    assert updated.status == "active"

    # Reload from disk to confirm persistence
    reloaded = client.get(dec.id)
    assert reloaded.status == "active"


def test_get_nonexistent_raises(tmp_dir: Path) -> None:
    """Getting a non-existent decision raises DecisionNotFoundError."""
    client = _make_client(tmp_dir)
    with pytest.raises(DecisionNotFoundError):
        client.get("dec_does_not_exist")
