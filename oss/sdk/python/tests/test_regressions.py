"""Regression tests covering the manual testing playbook scenarios."""

from __future__ import annotations

from multiprocessing import get_context
from pathlib import Path

from continuum.client import ContinuumClient


def _make_client(tmp_dir: Path) -> ContinuumClient:
    return ContinuumClient(storage_dir=tmp_dir / ".continuum")


def _inspect_in_process(store: str, target_scope: str, conn) -> None:  # type: ignore[no-untyped-def]
    client = ContinuumClient(storage_dir=store)
    conn.send(client.inspect(target_scope))
    conn.close()


def test_supersession_correctness(tmp_dir: Path) -> None:
    client = _make_client(tmp_dir)

    v1 = client.commit(
        title="production-ready",
        scope="repo:acme/backend",
        decision_type="interpretation",
        rationale="Production-ready means tests + error handling.",
        metadata={"selected_option_id": "opt_tests_errors"},
    )
    v1 = client.update_status(v1.id, "active")

    v2 = client.supersede(
        old_id=v1.id,
        new_title="production-ready",
        rationale="Production-ready now includes linting.",
        metadata={"selected_option_id": "opt_tests_errors_lint"},
    )

    v1_reloaded = client.get(v1.id)
    assert v1_reloaded.status == "superseded"
    assert v2.status == "active"
    assert v2.enforcement is not None
    assert v2.enforcement.supersedes == v1.id


def test_scope_filtering_and_binding_set(tmp_dir: Path) -> None:
    client = _make_client(tmp_dir)

    repo_dec = client.commit(
        title="Reject full rewrites",
        scope="repo:acme/backend",
        decision_type="rejection",
        rationale="Prefer incremental changes.",
    )
    client.update_status(repo_dec.id, "active")

    folder_dec = client.commit(
        title="Auth module uses DynamoDB",
        scope="repo:acme/backend/folder:src/api/auth",
        decision_type="preference",
        rationale="Token workload fits DynamoDB.",
    )
    client.update_status(folder_dec.id, "active")

    # Wildcard list: repo:* includes both repo-level and chained folder-level decisions.
    repo_star = client.list_decisions(scope="repo:*")
    repo_scopes = [
        (
            d.enforcement.get("scope")  # type: ignore[union-attr]
            if isinstance(d.enforcement, dict)
            else d.enforcement.scope  # type: ignore[union-attr]
        )
        for d in repo_star
        if d.enforcement is not None
    ]
    assert "repo:acme/backend" in repo_scopes
    assert "repo:acme/backend/folder:src/api/auth" in repo_scopes

    # Binding set at the folder scope includes the broader repo decision too.
    binding = client.inspect("repo:acme/backend/folder:src/api/auth")
    titles = {d["title"] for d in binding}
    assert "Reject full rewrites" in titles
    assert "Auth module uses DynamoDB" in titles


def test_override_policy_invalid_warn_allow(tmp_dir: Path) -> None:
    scope = "repo:acme/backend"

    # invalid_by_default -> block
    client = ContinuumClient(storage_dir=tmp_dir / "case_block" / ".continuum")
    dec_block = client.commit(
        title="Reject full rewrites",
        scope=scope,
        decision_type="rejection",
        override_policy="invalid_by_default",
        options=[
            {"title": "Incremental refactor", "selected": True},
            {"title": "Full rewrite", "selected": False, "rejected_reason": "Too risky"},
        ],
        rationale="Avoid rewrites.",
    )
    client.update_status(dec_block.id, "active")
    r_block = client.enforce(
        action={"type": "code_change", "description": "Do a full rewrite of auth module"},
        scope=scope,
    )
    assert r_block["verdict"] == "block"

    # warn -> confirm (warning verdict)
    client2 = ContinuumClient(storage_dir=tmp_dir / "case_warn" / ".continuum")
    dec_warn = client2.commit(
        title="Reject full rewrites (warn)",
        scope=scope,
        decision_type="rejection",
        override_policy="warn",
        options=[
            {"title": "Incremental refactor", "selected": True},
            {"title": "Full rewrite", "selected": False, "rejected_reason": "Too risky"},
        ],
        rationale="Avoid rewrites, but warn only.",
    )
    client2.update_status(dec_warn.id, "active")
    r_warn = client2.enforce(
        action={"type": "code_change", "description": "Do a full rewrite of auth module"},
        scope=scope,
    )
    assert r_warn["verdict"] == "confirm"

    # allow -> allow
    client3 = ContinuumClient(storage_dir=tmp_dir / "case_allow" / ".continuum")
    dec_allow = client3.commit(
        title="Reject full rewrites (allow)",
        scope=scope,
        decision_type="rejection",
        override_policy="allow",
        options=[
            {"title": "Incremental refactor", "selected": True},
            {"title": "Full rewrite", "selected": False, "rejected_reason": "Too risky"},
        ],
        rationale="Informational only.",
    )
    client3.update_status(dec_allow.id, "active")
    r_allow = client3.enforce(
        action={"type": "code_change", "description": "Do a full rewrite of auth module"},
        scope=scope,
    )
    assert r_allow["verdict"] == "allow"


def test_portability_two_processes_same_store(tmp_dir: Path) -> None:
    storage_dir = tmp_dir / ".continuum"
    scope = "repo:acme/backend"

    c1 = ContinuumClient(storage_dir=storage_dir)
    d = c1.commit(title="Prefer PostgreSQL", scope=scope, decision_type="preference", rationale="ACID")
    c1.update_status(d.id, "active")

    ctx = get_context("spawn")
    parent_conn, child_conn = ctx.Pipe(duplex=False)
    p = ctx.Process(target=_inspect_in_process, args=(str(storage_dir), scope, child_conn))
    p.start()
    binding = parent_conn.recv()
    p.join(timeout=5)

    assert any(b.get("title") == "Prefer PostgreSQL" for b in binding)

