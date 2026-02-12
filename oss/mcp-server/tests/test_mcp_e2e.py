"""End-to-end tests for the Continuum MCP server.

These tests exercise the MCP tool handlers directly (no stdio transport)
against a temporary store directory, covering the full lifecycle:
  commit -> inspect -> resolve -> enforce -> supersede

Plus new tests for:
  - Idempotent commit (same scope + title twice → same decision)
  - Auto-supersede (same key, different value → old superseded)
  - Null-key safety (binding_key fallback from title)
  - Effective bindings (inspect grouping by binding_key)
  - HttpBackend (mocked HTTP)
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
    # Ensure we're in local mode (no hosted API)
    monkeypatch.delenv("CONTINUUM_API_URL", raising=False)
    monkeypatch.delenv("CONTINUUM_BASE_URL", raising=False)


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

    def test_commit_with_key(self):
        result = _parse(_handle_commit({
            "title": "response.verbosity.default = short",
            "scope": "repo:test",
            "decision_type": "preference",
            "rationale": "Short by default.",
            "key": "response.verbosity.default",
            "activate": True,
        }))
        assert result["status"] == "active"
        enf = result.get("enforcement") or {}
        assert enf.get("key") == "response.verbosity.default"
        assert enf.get("binding_key") == "response.verbosity.default"
        assert enf.get("value_hash")  # non-empty


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
        # New shape: dict with bindings, conflict_notes, items
        assert isinstance(result, dict)
        assert "bindings" in result
        assert "conflict_notes" in result
        assert "items" in result
        assert len(result["bindings"]) >= 1
        # items should equal bindings (backward compat)
        assert result["items"] == result["bindings"]

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
# Idempotent commit
# ------------------------------------------------------------------


class TestIdempotentCommit:
    def test_same_commit_twice_returns_same_decision(self):
        """Committing the same (scope, title, rationale) twice should be idempotent."""
        args = {
            "title": "response.verbosity.default = short_unless_requested",
            "scope": "repo:idem-test",
            "decision_type": "preference",
            "rationale": "Short by default.",
            "activate": True,
        }
        first = _parse(_handle_commit(args))
        second = _parse(_handle_commit(args))

        # Idempotent: same decision ID returned
        assert first["id"] == second["id"]
        assert first["status"] == "active"

        # Inspect should show exactly one active binding
        result = _parse(_handle_inspect({"scope": "repo:idem-test"}))
        assert len(result["bindings"]) == 1
        assert result["bindings"][0]["id"] == first["id"]

    def test_idempotent_with_options(self):
        """Idempotency should also work when options are identical."""
        args = {
            "title": "Pick approach",
            "scope": "repo:idem-opts",
            "decision_type": "preference",
            "rationale": "Incremental wins.",
            "options": [
                {"id": "opt_a", "title": "Incremental", "selected": True},
                {"id": "opt_b", "title": "Full rewrite", "selected": False},
            ],
            "activate": True,
        }
        first = _parse(_handle_commit(args))
        second = _parse(_handle_commit(args))
        assert first["id"] == second["id"]


# ------------------------------------------------------------------
# Auto-supersede
# ------------------------------------------------------------------


class TestAutoSupersede:
    def test_same_key_different_value_auto_supersedes(self):
        """Committing a different value for the same key should auto-supersede."""
        first = _parse(_handle_commit({
            "title": "response.verbosity.default = verbose",
            "scope": "repo:auto-sup",
            "decision_type": "preference",
            "rationale": "Verbose mode.",
            "key": "response.verbosity.default",
            "activate": True,
        }))
        assert first["status"] == "active"

        second = _parse(_handle_commit({
            "title": "response.verbosity.default = concise",
            "scope": "repo:auto-sup",
            "decision_type": "preference",
            "rationale": "Concise mode.",
            "key": "response.verbosity.default",
            "activate": True,
        }))
        assert second["status"] == "active"
        assert second["id"] != first["id"]

        # First should now be superseded
        old = _parse(_handle_inspect({"decision_id": first["id"]}))
        assert old["status"] == "superseded"

        # Inspect should show only the second
        result = _parse(_handle_inspect({"scope": "repo:auto-sup"}))
        assert len(result["bindings"]) == 1
        assert result["bindings"][0]["id"] == second["id"]


# ------------------------------------------------------------------
# Null-key safety
# ------------------------------------------------------------------


class TestNullKeySafety:
    def test_no_explicit_key_uses_title_as_binding_key(self):
        """Without explicit key, title should be used as binding_key."""
        first = _parse(_handle_commit({
            "title": "Use tabs not spaces",
            "scope": "repo:null-key",
            "decision_type": "preference",
            "rationale": "Team convention.",
            "activate": True,
        }))

        # binding_key should equal title when no key provided
        enf = first.get("enforcement") or {}
        assert enf.get("binding_key") == "Use tabs not spaces"
        assert enf.get("key") is None

        # Second identical commit should be idempotent
        second = _parse(_handle_commit({
            "title": "Use tabs not spaces",
            "scope": "repo:null-key",
            "decision_type": "preference",
            "rationale": "Team convention.",
            "activate": True,
        }))
        assert second["id"] == first["id"]

        # Should have exactly one active
        result = _parse(_handle_inspect({"scope": "repo:null-key"}))
        assert len(result["bindings"]) == 1


# ------------------------------------------------------------------
# Inspect effective bindings
# ------------------------------------------------------------------


class TestInspectEffectiveBindings:
    def test_one_winner_per_binding_key(self):
        """Inspect should return one winner per binding_key."""
        # Create two decisions with different keys
        _parse(_handle_commit({
            "title": "Prefer tabs",
            "scope": "repo:eff-bind",
            "decision_type": "preference",
            "rationale": "Tabs.",
            "key": "formatting.indent",
            "activate": True,
        }))
        _parse(_handle_commit({
            "title": "Use English",
            "scope": "repo:eff-bind",
            "decision_type": "preference",
            "rationale": "English.",
            "key": "response.language",
            "activate": True,
        }))

        result = _parse(_handle_inspect({"scope": "repo:eff-bind"}))
        assert len(result["bindings"]) == 2
        binding_keys = {
            (b.get("enforcement") or {}).get("binding_key")
            for b in result["bindings"]
        }
        assert binding_keys == {"formatting.indent", "response.language"}
        assert result["conflict_notes"] == []


# ------------------------------------------------------------------
# HttpBackend (unit test with mocked HTTP)
# ------------------------------------------------------------------


class TestHttpBackend:
    def test_commit_calls_correct_endpoint(self, monkeypatch):
        """HttpBackend.commit() should POST to /commit."""
        from continuum_mcp.http_backend import HttpBackend

        captured = {}

        def mock_request(self, method, path, body=None, params=None):
            captured["method"] = method
            captured["path"] = path
            captured["body"] = body
            return {
                "decision": {
                    "id": "dec_mock123",
                    "title": "Test",
                    "status": "draft",
                }
            }

        monkeypatch.setattr(HttpBackend, "_request", mock_request)
        be = HttpBackend(base_url="http://localhost:8787", api_key="test-key")
        result = be.commit(
            title="Test",
            scope="repo:test",
            decision_type="preference",
            rationale="Testing.",
            key="test.key",
        )
        assert captured["method"] == "POST"
        assert captured["path"] == "/commit"
        assert captured["body"]["key"] == "test.key"
        assert result["id"] == "dec_mock123"

    def test_inspect_calls_correct_endpoint(self, monkeypatch):
        """HttpBackend.inspect() should GET /inspect?scope=..."""
        from continuum_mcp.http_backend import HttpBackend

        captured = {}

        def mock_request(self, method, path, body=None, params=None):
            captured["method"] = method
            captured["path"] = path
            captured["params"] = params
            return {
                "binding": [{"id": "dec_1", "title": "T"}],
                "conflict_notes": [],
            }

        monkeypatch.setattr(HttpBackend, "_request", mock_request)
        be = HttpBackend(base_url="http://localhost:8787")
        result = be.inspect("repo:test")
        assert captured["method"] == "GET"
        assert captured["path"] == "/inspect"
        assert captured["params"] == {"scope": "repo:test"}
        assert "bindings" in result

    def test_update_status_calls_patch(self, monkeypatch):
        """HttpBackend.update_status() should PATCH /decision/{id}/status."""
        from continuum_mcp.http_backend import HttpBackend

        captured = {}

        def mock_request(self, method, path, body=None, params=None):
            captured["method"] = method
            captured["path"] = path
            captured["body"] = body
            return {"decision": {"id": "dec_abc", "status": "active"}}

        monkeypatch.setattr(HttpBackend, "_request", mock_request)
        be = HttpBackend(base_url="http://localhost:8787")
        result = be.update_status("dec_abc", "active")
        assert captured["method"] == "PATCH"
        assert captured["path"] == "/decision/dec_abc/status"
        assert captured["body"] == {"status": "active"}
        assert result["status"] == "active"

    def test_supersede_calls_post(self, monkeypatch):
        """HttpBackend.supersede() should POST /supersede."""
        from continuum_mcp.http_backend import HttpBackend

        captured = {}

        def mock_request(self, method, path, body=None, params=None):
            captured["method"] = method
            captured["path"] = path
            captured["body"] = body
            return {"decision": {"id": "dec_new", "status": "active"}}

        monkeypatch.setattr(HttpBackend, "_request", mock_request)
        be = HttpBackend(base_url="http://localhost:8787")
        result = be.supersede(old_id="dec_old", new_title="V2")
        assert captured["method"] == "POST"
        assert captured["path"] == "/supersede"
        assert captured["body"]["old_id"] == "dec_old"
        assert result["status"] == "active"


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

        # 2. Inspect by scope — returns new dict shape
        result = _parse(_handle_inspect({"scope": scope}))
        assert isinstance(result, dict)
        assert any(d["id"] == dec_id for d in result["bindings"])

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
        final = _parse(_handle_inspect({"scope": scope}))
        active_ids = [d["id"] for d in final["bindings"]]
        assert new_dec["id"] in active_ids
        assert dec_id not in active_ids  # Old decision should be superseded
