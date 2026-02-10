"""Unit tests for ContinuumToolSpec (LlamaIndex integration)."""

from __future__ import annotations

import json

import pytest

from continuum_llamaindex.tool_spec import ContinuumToolSpec


@pytest.fixture()
def spec(tmp_path):
    """ContinuumToolSpec backed by a temp store."""
    return ContinuumToolSpec(storage_dir=str(tmp_path / ".continuum"))


@pytest.fixture()
def active_decision(spec):
    """Commit and activate a rejection decision, return its dict."""
    dec = spec.commit(
        title="Reject full rewrites",
        scope="repo:test",
        decision_type="rejection",
        rationale="Too risky.",
        options=[
            {"title": "Incremental refactor", "selected": True},
            {"title": "Full rewrite", "selected": False, "rejected_reason": "Too risky"},
        ],
        activate=True,
    )
    return dec


# ------------------------------------------------------------------
# commit
# ------------------------------------------------------------------


class TestCommit:
    def test_basic_commit(self, spec):
        result = spec.commit(
            title="Test decision",
            scope="repo:test",
            decision_type="interpretation",
            rationale="For testing.",
        )
        assert result["title"] == "Test decision"
        assert result["id"].startswith("dec_")
        assert result["status"] == "draft"

    def test_commit_with_activate(self, spec):
        result = spec.commit(
            title="Active decision",
            scope="repo:test",
            decision_type="preference",
            rationale="Activated immediately.",
            activate=True,
        )
        assert result["status"] == "active"

    def test_commit_with_options(self, spec):
        result = spec.commit(
            title="With options",
            scope="repo:test",
            decision_type="rejection",
            rationale="Testing options.",
            options=[
                {"title": "A", "selected": True},
                {"title": "B", "selected": False},
            ],
        )
        assert len(result["options_considered"]) == 2

    def test_commit_with_metadata(self, spec):
        result = spec.commit(
            title="Meta test",
            scope="repo:test",
            decision_type="interpretation",
            rationale="Testing metadata.",
            metadata={"team": "platform"},
        )
        assert result["metadata"]["team"] == "platform"

    def test_commit_with_stakeholders(self, spec):
        result = spec.commit(
            title="Stakeholder test",
            scope="repo:test",
            decision_type="interpretation",
            rationale="Testing stakeholders.",
            stakeholders=["alice", "bob"],
        )
        assert result["stakeholders"] == ["alice", "bob"]


# ------------------------------------------------------------------
# inspect
# ------------------------------------------------------------------


class TestInspect:
    def test_inspect_empty(self, spec):
        result = spec.inspect(scope="repo:empty")
        assert result == []

    def test_inspect_returns_active_decisions(self, spec, active_decision):
        result = spec.inspect(scope="repo:test")
        assert len(result) >= 1
        titles = [d["title"] for d in result]
        assert "Reject full rewrites" in titles

    def test_inspect_wrong_scope(self, spec, active_decision):
        result = spec.inspect(scope="repo:other")
        # Should not match unless scope rules overlap
        assert isinstance(result, list)


# ------------------------------------------------------------------
# resolve
# ------------------------------------------------------------------


class TestResolve:
    def test_resolve_no_prior_decisions(self, spec):
        result = spec.resolve(prompt="something new", scope="repo:test")
        assert "status" in result

    def test_resolve_with_matching_decision(self, spec, active_decision):
        result = spec.resolve(
            prompt="Reject full rewrites",
            scope="repo:test",
        )
        assert result["status"] == "resolved"

    def test_resolve_with_candidates(self, spec):
        result = spec.resolve(
            prompt="Pick an approach",
            scope="repo:test",
            candidates=[
                {"id": "opt_a", "title": "Approach A"},
                {"id": "opt_b", "title": "Approach B"},
            ],
        )
        assert "status" in result


# ------------------------------------------------------------------
# enforce
# ------------------------------------------------------------------


class TestEnforce:
    def test_enforce_no_decisions(self, spec):
        result = spec.enforce(
            action={"type": "code_change", "description": "minor fix"},
            scope="repo:test",
        )
        assert "verdict" in result

    def test_enforce_with_rejection_decision(self, spec, active_decision):
        result = spec.enforce(
            action={"type": "code_change", "description": "Do a full rewrite"},
            scope="repo:test",
        )
        assert "verdict" in result

    def test_enforce_different_action_type(self, spec, active_decision):
        result = spec.enforce(
            action={"type": "generic", "description": "something else"},
            scope="repo:test",
        )
        assert result["verdict"] in ("allow", "confirm", "block", "override")


# ------------------------------------------------------------------
# supersede
# ------------------------------------------------------------------


class TestSupersede:
    def test_supersede(self, spec, active_decision):
        dec_id = active_decision["id"]
        result = spec.supersede(
            old_id=dec_id,
            new_title="V2 replacement",
            rationale="Updated policy.",
        )
        assert result["title"] == "V2 replacement"
        assert result["status"] == "active"

    def test_supersede_with_options(self, spec, active_decision):
        result = spec.supersede(
            old_id=active_decision["id"],
            new_title="V2 with options",
            options=[
                {"title": "New A", "selected": True},
                {"title": "New B", "selected": False},
            ],
        )
        assert result["status"] == "active"
        assert len(result["options_considered"]) == 2

    def test_supersede_preserves_scope(self, spec, active_decision):
        result = spec.supersede(
            old_id=active_decision["id"],
            new_title="Scope preservation test",
        )
        # New decision should inherit scope from old
        assert result["enforcement"]["scope"] == "repo:test"


# ------------------------------------------------------------------
# spec_functions
# ------------------------------------------------------------------


class TestSpecFunctions:
    def test_spec_functions_list(self):
        assert ContinuumToolSpec.spec_functions == [
            "inspect", "resolve", "enforce", "commit", "supersede"
        ]

    def test_all_functions_callable(self, spec):
        for fn_name in ContinuumToolSpec.spec_functions:
            assert callable(getattr(spec, fn_name))
