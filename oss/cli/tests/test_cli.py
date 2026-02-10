"""Tests for the Continuum CLI using typer.testing.CliRunner."""

from __future__ import annotations

import json
import os
import tempfile

import pytest
from typer.testing import CliRunner

from continuum_cli.main import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def _use_temp_store(monkeypatch: pytest.MonkeyPatch, tmp_path):
    """Point the CLI at a temp directory so tests don't pollute the real store."""
    store = tmp_path / ".continuum"
    monkeypatch.chdir(tmp_path)
    yield store


# ------------------------------------------------------------------
# commit
# ------------------------------------------------------------------


class TestCommit:
    def test_basic_commit(self):
        result = runner.invoke(
            app,
            ["commit", "Reject rewrites", "--scope", "repo:test", "--type", "rejection"],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["title"] == "Reject rewrites"
        assert data["id"].startswith("dec_")

    def test_commit_with_rationale(self):
        result = runner.invoke(
            app,
            [
                "commit", "Prefer REST",
                "--scope", "api",
                "--type", "preference",
                "--rationale", "REST is well-understood.",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["rationale"] == "REST is well-understood."

    def test_commit_with_options_and_activate(self):
        opts = json.dumps([{"title": "Option A", "selected": True}, {"title": "Option B", "selected": False}])
        result = runner.invoke(
            app,
            [
                "commit", "Pick A",
                "--scope", "repo:test",
                "--type", "preference",
                "--options", opts,
                "--activate",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["status"] == "active"
        assert len(data["options_considered"]) == 2

    def test_commit_with_metadata(self):
        meta = json.dumps({"team": "platform"})
        result = runner.invoke(
            app,
            [
                "commit", "Meta decision",
                "--scope", "repo:test",
                "--type", "interpretation",
                "--metadata", meta,
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["metadata"]["team"] == "platform"

    def test_commit_bad_options_json(self):
        result = runner.invoke(
            app,
            ["commit", "Bad", "--scope", "x", "--type", "rejection", "--options", "not-json"],
        )
        assert result.exit_code == 1


# ------------------------------------------------------------------
# inspect
# ------------------------------------------------------------------


class TestInspect:
    def test_inspect_by_id(self):
        # First commit a decision
        result = runner.invoke(
            app,
            ["commit", "Test decision", "--scope", "repo:inspect-test", "--type", "rejection"],
        )
        assert result.exit_code == 0
        dec_id = json.loads(result.stdout)["id"]

        # Inspect by ID
        result = runner.invoke(app, ["inspect", dec_id])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["id"] == dec_id

    def test_inspect_by_scope(self):
        # Commit and activate a decision
        result = runner.invoke(
            app,
            ["commit", "Scoped decision", "--scope", "repo:scope-test", "--type", "rejection", "--activate"],
        )
        assert result.exit_code == 0

        # Inspect by scope
        result = runner.invoke(app, ["inspect", "--scope", "repo:scope-test"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_inspect_no_args(self):
        result = runner.invoke(app, ["inspect"])
        assert result.exit_code == 1

    def test_inspect_both_args(self):
        result = runner.invoke(app, ["inspect", "dec_123", "--scope", "repo:x"])
        assert result.exit_code == 1


# ------------------------------------------------------------------
# resolve
# ------------------------------------------------------------------


class TestResolve:
    def test_resolve_needs_clarification(self):
        result = runner.invoke(
            app,
            ["resolve", "Make it production-ready", "--scope", "repo:test"],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "status" in data

    def test_resolve_with_prior_decision(self):
        # Commit and activate a rejection decision
        runner.invoke(
            app,
            ["commit", "Reject full rewrites", "--scope", "repo:resolve-test", "--type", "rejection", "--activate"],
        )

        result = runner.invoke(
            app,
            ["resolve", "Reject full rewrites", "--scope", "repo:resolve-test"],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["status"] == "resolved"

    def test_resolve_bad_candidates_json(self):
        result = runner.invoke(
            app,
            ["resolve", "test", "--scope", "x", "--candidates", "bad-json"],
        )
        assert result.exit_code == 1


# ------------------------------------------------------------------
# enforce
# ------------------------------------------------------------------


class TestEnforce:
    def test_enforce_allow(self):
        result = runner.invoke(
            app,
            [
                "enforce",
                "--scope", "repo:test",
                "--action-detail", '{"description":"add a test"}',
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "verdict" in data

    def test_enforce_with_rejection(self):
        # Seed a rejection decision
        runner.invoke(
            app,
            [
                "commit", "Reject full rewrites",
                "--scope", "repo:enforce-test",
                "--type", "rejection",
                "--options", json.dumps([
                    {"title": "Incremental refactor", "selected": True},
                    {"title": "Full rewrite", "selected": False, "rejected_reason": "Too risky"},
                ]),
                "--activate",
            ],
        )

        result = runner.invoke(
            app,
            [
                "enforce",
                "--scope", "repo:enforce-test",
                "--action-type", "code_change",
                "--action-detail", '{"description":"Do a full rewrite of auth module"}',
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "verdict" in data

    def test_enforce_bad_json(self):
        result = runner.invoke(
            app,
            ["enforce", "--scope", "x", "--action-detail", "not-json"],
        )
        assert result.exit_code == 1


# ------------------------------------------------------------------
# list
# ------------------------------------------------------------------


class TestList:
    def test_list_empty(self):
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "No decisions found" in result.stdout

    def test_list_with_decisions(self):
        runner.invoke(
            app,
            ["commit", "Decision A", "--scope", "repo:list-test", "--type", "rejection"],
        )
        runner.invoke(
            app,
            ["commit", "Decision B", "--scope", "repo:list-test", "--type", "preference"],
        )

        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "Decision A" in result.stdout
        assert "Decision B" in result.stdout

    def test_list_filter_by_scope(self):
        runner.invoke(
            app,
            ["commit", "Scoped", "--scope", "repo:filtered", "--type", "rejection"],
        )
        runner.invoke(
            app,
            ["commit", "Other", "--scope", "repo:other", "--type", "rejection"],
        )

        result = runner.invoke(app, ["list", "--scope", "repo:filtered"])
        assert result.exit_code == 0
        assert "Scoped" in result.stdout

    def test_list_filter_by_status(self):
        res = runner.invoke(
            app,
            ["commit", "Active one", "--scope", "repo:status-test", "--type", "rejection", "--activate"],
        )
        runner.invoke(
            app,
            ["commit", "Draft one", "--scope", "repo:status-test", "--type", "rejection"],
        )

        result = runner.invoke(app, ["list", "--status", "active"])
        assert result.exit_code == 0
        assert "Active one" in result.stdout

    def test_list_json_output(self):
        runner.invoke(
            app,
            ["commit", "JSON test", "--scope", "repo:json", "--type", "rejection"],
        )
        result = runner.invoke(app, ["list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)


# ------------------------------------------------------------------
# supersede
# ------------------------------------------------------------------


class TestSupersede:
    def test_simple_supersede(self):
        # Commit and activate a decision
        res = runner.invoke(
            app,
            ["commit", "Original", "--scope", "repo:sup-test", "--type", "rejection", "--activate"],
        )
        dec_id = json.loads(res.stdout)["id"]

        result = runner.invoke(app, ["supersede", dec_id])
        assert result.exit_code == 0
        assert "superseded" in result.stdout

    def test_full_replacement_supersede(self):
        # Commit and activate a decision
        res = runner.invoke(
            app,
            ["commit", "V1", "--scope", "repo:sup-full", "--type", "rejection", "--activate"],
        )
        dec_id = json.loads(res.stdout)["id"]

        result = runner.invoke(
            app,
            [
                "supersede", dec_id,
                "--new-title", "V2 replacement",
                "--rationale", "Updated approach",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["title"] == "V2 replacement"
        assert data["status"] == "active"


# ------------------------------------------------------------------
# scopes
# ------------------------------------------------------------------


class TestScopes:
    def test_scopes_empty(self):
        result = runner.invoke(app, ["scopes"])
        assert result.exit_code == 0
        assert "No scopes found" in result.stdout

    def test_scopes_with_data(self):
        runner.invoke(
            app,
            ["commit", "S1", "--scope", "repo:scope-a", "--type", "rejection", "--activate"],
        )
        runner.invoke(
            app,
            ["commit", "S2", "--scope", "repo:scope-b", "--type", "rejection"],
        )

        result = runner.invoke(app, ["scopes"])
        assert result.exit_code == 0
        assert "repo:scope-a" in result.stdout
