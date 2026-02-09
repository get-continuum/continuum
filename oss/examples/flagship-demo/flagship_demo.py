#!/usr/bin/env python3
"""Flagship end-to-end demo for the Continuum decision framework.

Proves:
  1. Decision persistence (file-backed)
  2. Rejection binding ("full rewrite" becomes invalid)
  3. Ambiguity gate ("production-ready" — clarified once, then remembered)
  4. Supersession (v1 → v2 updates the binding set deterministically)
  5. Enforcement engine blocks banned actions
  6. Resolve returns cached interpretation on second call

Usage:
    pip install continuum-sdk
    python oss/examples/flagship-demo/flagship_demo.py
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from continuum.client import ContinuumClient


SEPARATOR = "=" * 60


def main() -> None:
    # Use a temporary .continuum directory so we start clean
    repo_root = Path(__file__).resolve().parents[3]
    store_dir = repo_root / ".continuum-demo"

    # Clean up from any previous run
    if store_dir.exists():
        shutil.rmtree(store_dir)

    client = ContinuumClient(storage_dir=str(store_dir))
    scope = "repo:continuum"

    passed = 0
    failed = 0

    # -----------------------------------------------------------------
    # 1) Commit a REJECTION decision: no full rewrites
    # -----------------------------------------------------------------
    print(f"\n{SEPARATOR}")
    print("1) Commit a REJECTION decision: no full rewrites")
    print(SEPARATOR)

    reject_dec = client.commit(
        title="Reject full rewrites in this repo",
        scope=scope,
        decision_type="rejection",
        options=[
            {"id": "opt_incremental", "title": "Incremental refactor", "selected": True},
            {
                "id": "opt_full_rewrite",
                "title": "Full rewrite",
                "selected": False,
                "rejected_reason": "Too risky; prefer incremental refactors.",
            },
        ],
        rationale="Prefer incremental refactors to reduce risk and review cost.",
    )
    # Activate it immediately
    reject_dec = client.update_status(reject_dec.id, "active")
    print(f"   Committed & activated: {reject_dec.id}")
    print(f"   Status: {reject_dec.status}")
    assert reject_dec.status == "active", "Decision should be active"
    passed += 1

    # -----------------------------------------------------------------
    # 2) Inspect binding decisions (should include rejection)
    # -----------------------------------------------------------------
    print(f"\n{SEPARATOR}")
    print("2) Inspect binding decisions (should include rejection)")
    print(SEPARATOR)

    binding = client.inspect(scope)
    print(f"   Active decisions in scope '{scope}': {len(binding)}")
    print(json.dumps(binding, indent=2, default=str))
    assert len(binding) >= 1, "Should have at least 1 active decision"
    assert any(
        d["title"] == "Reject full rewrites in this repo" for d in binding
    ), "Rejection decision should be in binding set"
    passed += 1

    # -----------------------------------------------------------------
    # 3) Enforce a plan containing a banned step (should BLOCK)
    # -----------------------------------------------------------------
    print(f"\n{SEPARATOR}")
    print("3) Enforce a plan with banned step (should BLOCK)")
    print(SEPARATOR)

    action = {
        "type": "code_change",
        "description": "Do a full rewrite of auth module",
    }
    result = client.enforce(action, scope)
    print(f"   Verdict: {result['verdict']}")
    print(f"   Reason:  {result['reason']}")
    assert result["verdict"] == "block", (
        f"Expected 'block', got '{result['verdict']}'"
    )
    passed += 1

    # Verify that a non-banned action is allowed
    safe_action = {
        "type": "code_change",
        "description": "Add error handling to auth module",
    }
    safe_result = client.enforce(safe_action, scope)
    print(f"\n   Safe action verdict: {safe_result['verdict']}")
    assert safe_result["verdict"] == "allow", (
        f"Expected 'allow', got '{safe_result['verdict']}'"
    )
    passed += 1

    # -----------------------------------------------------------------
    # 4) Ambiguity Gate: "production-ready" (first call → needs_clarification)
    # -----------------------------------------------------------------
    print(f"\n{SEPARATOR}")
    print("4) Ambiguity Gate: 'Make this production-ready' (first call)")
    print(SEPARATOR)

    query = "Make this production-ready"
    candidates = [
        {"id": "opt_tests_errors", "title": "Add tests + error handling (repo standard)"},
        {"id": "opt_enterprise", "title": "Enterprise hardening (observability, SLOs, etc.)"},
    ]

    res1 = client.resolve(query=query, scope=scope, candidates=candidates)
    print(f"   Status: {res1['status']}")
    assert res1["status"] == "needs_clarification", (
        f"Expected 'needs_clarification', got '{res1['status']}'"
    )
    print("   Clarification:", json.dumps(res1.get("clarification"), indent=4))
    passed += 1

    # -----------------------------------------------------------------
    # Simulate user choosing "tests + errors" and committing interpretation
    # -----------------------------------------------------------------
    print(f"\n{SEPARATOR}")
    print("   User chose: 'Add tests + error handling'")
    print(SEPARATOR)

    interp_dec = client.commit(
        title="production-ready",
        scope=scope,
        decision_type="interpretation",
        rationale="In this repo, production-ready means tests + error handling.",
        metadata={"selected_option_id": "opt_tests_errors"},
    )
    interp_dec = client.update_status(interp_dec.id, "active")
    print(f"   Committed interpretation: {interp_dec.id}")

    # -----------------------------------------------------------------
    # 5) Resolve again (should return resolved — no gate)
    # -----------------------------------------------------------------
    print(f"\n{SEPARATOR}")
    print("5) Resolve again (should return 'resolved' — no gate)")
    print(SEPARATOR)

    res2 = client.resolve(query=query, scope=scope, candidates=candidates)
    print(f"   Status: {res2['status']}")
    assert res2["status"] == "resolved", (
        f"Expected 'resolved', got '{res2['status']}'"
    )
    print(f"   Matched decision: {res2.get('matched_decision_id')}")
    passed += 1

    # -----------------------------------------------------------------
    # 6) Supersede the interpretation (v1 → v2)
    # -----------------------------------------------------------------
    print(f"\n{SEPARATOR}")
    print("6) Supersede interpretation: tests+errors → tests+errors+lint")
    print(SEPARATOR)

    new_dec = client.supersede(
        old_id=interp_dec.id,
        new_title="production-ready",
        rationale="Production-ready now includes tests + error handling + lint.",
        metadata={"selected_option_id": "opt_tests_errors_lint"},
    )
    print(f"   Old decision {interp_dec.id} → superseded")
    print(f"   New decision {new_dec.id} → active")

    # Verify old is superseded
    old_reloaded = client.get(interp_dec.id)
    assert old_reloaded.status == "superseded", (
        f"Old decision should be superseded, got '{old_reloaded.status}'"
    )
    assert new_dec.status == "active", (
        f"New decision should be active, got '{new_dec.status}'"
    )
    passed += 1

    # -----------------------------------------------------------------
    # 7) Inspect again (binding set should reflect v2, not v1)
    # -----------------------------------------------------------------
    print(f"\n{SEPARATOR}")
    print("7) Inspect binding set after supersession")
    print(SEPARATOR)

    binding2 = client.inspect(scope)
    active_ids = [d["id"] for d in binding2]

    print(f"   Active decisions: {len(binding2)}")
    for d in binding2:
        print(f"     - {d['id']}: {d['title']} (status={d['status']})")

    assert interp_dec.id not in active_ids, (
        "Superseded decision should NOT be in binding set"
    )
    assert new_dec.id in active_ids, (
        "New decision should be in binding set"
    )
    # Should have 2 active: rejection + new interpretation
    assert len(binding2) == 2, (
        f"Expected 2 active decisions, got {len(binding2)}"
    )
    passed += 1

    # -----------------------------------------------------------------
    # 8) Verify file persistence
    # -----------------------------------------------------------------
    print(f"\n{SEPARATOR}")
    print("8) Verify file persistence")
    print(SEPARATOR)

    decision_files = list((store_dir / "decisions").glob("*.json"))
    print(f"   Decision files on disk: {len(decision_files)}")
    for f in sorted(decision_files):
        print(f"     - {f.name}")

    assert len(decision_files) >= 3, (
        f"Expected at least 3 decision files, got {len(decision_files)}"
    )
    passed += 1

    # -----------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------
    total = passed + failed
    print(f"\n{'=' * 60}")
    print(f"RESULTS: {passed}/{total} checks passed")
    if failed:
        print(f"   {failed} FAILED")
        sys.exit(1)
    else:
        print("   ALL CHECKS PASSED")
    print(f"   Decisions stored at: {store_dir}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
