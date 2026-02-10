"""End-to-end tests for the Continuum MCP server.

These tests exercise the MCP tool handlers directly (no stdio transport)
against a temporary store directory, covering the full lifecycle:
  commit -> inspect -> resolve -> enforce -> supersede
"""

from __future__ import annotations

import json
import os

import pytest

# Import handlers directly for fast, reliable testing without MCP transport.
from continuum_mcp.server import (
    _handle_commit,
    _handle_enforce,
    _handle_inspect,
    _handle_resolve,
    _handle_supersede,
)


@pytest.fixture(autouse=True)
def _use_temp_store(tmp_path, monkeypatch):
    """Point the MCP server at a temp store."""
    store = str(tmp_path / ".continuum")
    monkeypatch.setenv("CONTINUUM_STORE", store)


def _parse(result: str) -> dict:
    """Parse a handler JSON response."""
    data = json.loads(result)
    assert data["status"] == "ok", f"Handler error: {data.get('error')}"
    return data["result"]


def _parse_err(result: str) -> str:
    """Parse a handler error response."""
    data = json.loads(result)
    assert data["status"] == "error"
    return data["error"]


# ------------------------------------------------------------------
# commit
# ------------------------------------------------------------------


class TestCommit:
    def test_basic_commit(self):
        result = _parse(_handle_commit({
            "title": "Test decision",
            "scope": "repo:test",
            "decision_type": "rejection",
            "rationale": "For testing.",
        }))
        assert result["title"] == "Test decision"
        assert result["id"].startswith("dec_")
        assert result["status"] == "draft"

    def test_commit_with_activate(self):
        result = _parse(_handle_commit({
            "title": "Active decision",
            "scope": "repo:test",
            "decision_type": "preference",
            "rationale": "Immediately active.",
            "activate": True,
        }))
        assert result["status"] == "active"

    def test_commit_with_options(self):
        result = _parse(_handle_commit({
            "title": "With options",
            "scope": "repo:test",
            "decision_type": "rejection",
            "rationale": "Testing options.",
            "options": [
                {"title": "A", "selected": True},
                {"title": "B", "selected": False, "rejected_reason": "Not chosen"},
            ],
        }))
        assert len(result["options_considered"]) == 2

    def test_commit_with_full_params(self):
        result = _parse(_handle_commit({
            "title": "Full params",
            "scope": "repo:test",
            "decision_type": "interpretation",
            "rationale": "Testing all params.",
            "stakeholders": ["alice", "bob"],
            "metadata": {"team": "platform"},
            "override_policy": "warn",
            "precedence": 10,
        }))
        assert result["stakeholders"] == ["alice", "bob"]
        assert result["metadata"]["team"] == "platform"

    def test_commit_missing_required(self):
        raw = _handle_commit({"title": "Missing scope"})
        data = json.loads(raw)
        assert data["status"] == "error"


# ------------------------------------------------------------------
# inspect
# ------------------------------------------------------------------


class TestInspect:
    def test_inspect_by_id(self):
        dec = _parse(_handle_commit({
            "title": "Inspectable",
            "scope": "repo:test",
            "decision_type": "rejection",
            "rationale": "For inspect test.",
        }))
        result = _parse(_handle_inspect({"decision_id": dec["id"]}))
        assert result["id"] == dec["id"]

    def test_inspect_by_scope(self):
        _parse(_handle_commit({
            "title": "Scope inspect",
            "scope": "repo:inspect-scope",
            "decision_type": "rejection",
            "rationale": "For scope test.",
            "activate": True,
        }))
        result = _parse(_handle_inspect({"scope": "repo:inspect-scope"}))
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_inspect_no_args(self):
        err = _parse_err(_handle_inspect({}))
        assert "Provide either" in err

    def test_inspect_nonexistent_id(self):
        err = _parse_err(_handle_inspect({"decision_id": "dec_nonexistent"}))
        assert "not found" in err.lower()


# ------------------------------------------------------------------
# resolve
# ------------------------------------------------------------------


class TestResolve:
    def test_resolve_no_decisions(self):
        result = _parse(_handle_resolve({
            "prompt": "something new",
            "scope": "repo:test",
        }))
        assert "status" in result

    def test_resolve_with_matching_decision(self):
        _parse(_handle_commit({
            "title": "Reject full rewrites",
            "scope": "repo:resolve-test",
            "decision_type": "rejection",
            "rationale": "Too risky.",
            "activate": True,
        }))
        result = _parse(_handle_resolve({
            "prompt": "Reject full rewrites",
            "scope": "repo:resolve-test",
        }))
        assert result["status"] == "resolved"

    def test_resolve_with_candidates(self):
        result = _parse(_handle_resolve({
            "prompt": "Pick approach",
            "scope": "repo:test",
            "candidates": [
                {"id": "a", "title": "Approach A"},
                {"id": "b", "title": "Approach B"},
            ],
        }))
        assert "status" in result


# ------------------------------------------------------------------
# enforce
# ------------------------------------------------------------------


class TestEnforce:
    def test_enforce_no_decisions(self):
        result = _parse(_handle_enforce({
            "scope": "repo:test",
            "action": {"type": "code_change", "description": "minor fix"},
        }))
        assert "verdict" in result

    def test_enforce_with_rejection(self):
        _parse(_handle_commit({
            "title": "Reject full rewrites",
            "scope": "repo:enforce-test",
            "decision_type": "rejection",
            "rationale": "Too risky.",
            "options": [
                {"title": "Incremental refactor", "selected": True},
                {"title": "Full rewrite", "selected": False, "rejected_reason": "Too risky"},
            ],
            "activate": True,
        }))
        result = _parse(_handle_enforce({
            "scope": "repo:enforce-test",
            "action": {"type": "code_change", "description": "Do a full rewrite of auth"},
        }))
        assert "verdict" in result


# ------------------------------------------------------------------
# supersede
# ------------------------------------------------------------------


class TestSupersede:
    def test_supersede_lifecycle(self):
        # Commit and activate
        dec = _parse(_handle_commit({
            "title": "V1 decision",
            "scope": "repo:supersede-test",
            "decision_type": "rejection",
            "rationale": "Original.",
            "activate": True,
        }))
        assert dec["status"] == "active"

        # Supersede
        new_dec = _parse(_handle_supersede({
            "old_id": dec["id"],
            "new_title": "V2 decision",
            "rationale": "Updated approach.",
        }))
        assert new_dec["title"] == "V2 decision"
        assert new_dec["status"] == "active"

        # Verify old is superseded
        old = _parse(_handle_inspect({"decision_id": dec["id"]}))
        assert old["status"] == "superseded"

    def test_supersede_nonexistent(self):
        err = _parse_err(_handle_supersede({
            "old_id": "dec_nonexistent",
            "new_title": "Won't work",
        }))
        assert "not found" in err.lower()


# ------------------------------------------------------------------
# Full lifecycle (integration)
# ------------------------------------------------------------------


class TestFullLifecycle:
    def test_commit_inspect_resolve_enforce_supersede(self):
        scope = "repo:lifecycle"

        # 1. Commit
        dec = _parse(_handle_commit({
            "title": "Reject full rewrites",
            "scope": scope,
            "decision_type": "rejection",
            "rationale": "Too risky.",
            "options": [
                {"title": "Incremental refactor", "selected": True},
                {"title": "Full rewrite", "selected": False, "rejected_reason": "Too risky"},
            ],
            "activate": True,
        }))
        dec_id = dec["id"]

        # 2. Inspect by scope
        binding = _parse(_handle_inspect({"scope": scope}))
        assert any(d["id"] == dec_id for d in binding)

        # 3. Resolve
        resolved = _parse(_handle_resolve({
            "prompt": "Reject full rewrites",
            "scope": scope,
        }))
        assert resolved["status"] == "resolved"

        # 4. Enforce
        enforcement = _parse(_handle_enforce({
            "scope": scope,
            "action": {"type": "code_change", "description": "full rewrite"},
        }))
        assert "verdict" in enforcement

        # 5. Supersede
        new_dec = _parse(_handle_supersede({
            "old_id": dec_id,
            "new_title": "V2: Allow rewrites for tests only",
            "rationale": "Relaxed policy for test modules.",
        }))
        assert new_dec["status"] == "active"

        # 6. Verify final state
        final_binding = _parse(_handle_inspect({"scope": scope}))
        active_ids = [d["id"] for d in final_binding]
        assert new_dec["id"] in active_ids
        assert dec_id not in active_ids  # Old decision should be superseded
