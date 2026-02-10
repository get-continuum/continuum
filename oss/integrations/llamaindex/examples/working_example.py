#!/usr/bin/env python3
"""Working LlamaIndex example using Continuum.

Demonstrates the ContinuumToolSpec adapter:
  1. Commit a rejection decision
  2. Resolve a prompt against it
  3. Enforce an action
  4. Inspect the binding set
  5. Supersede the decision

Run (after installing deps):
  pip install continuum-sdk continuum-llamaindex
  python oss/integrations/llamaindex/examples/working_example.py
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from continuum_llamaindex import ContinuumToolSpec


def main() -> None:
    # Use a local demo store (cleaned up at the end).
    storage_dir = ".continuum-llamaindex-demo"
    scope = "repo:llamaindex-demo"

    # Clean up any previous run.
    shutil.rmtree(storage_dir, ignore_errors=True)

    spec = ContinuumToolSpec(storage_dir=storage_dir)

    # --- Step 1: Commit a rejection decision ---
    print("1. Committing a rejection decision...")
    committed = spec.commit(
        title="Reject full rewrites",
        scope=scope,
        decision_type="rejection",
        rationale="Full rewrites carry too much risk. Prefer incremental refactors.",
        options=[
            {"title": "Incremental refactor", "selected": True},
            {"title": "Full rewrite", "selected": False, "rejected_reason": "Too risky"},
        ],
        activate=True,
    )
    dec_id = committed["id"]
    print(f"   Created: {dec_id} (status: {committed['status']})")

    # --- Step 2: Resolve a prompt ---
    print("\n2. Resolving 'Reject full rewrites' against prior decisions...")
    resolution = spec.resolve(
        prompt="Reject full rewrites",
        scope=scope,
    )
    print(f"   Status: {resolution['status']}")
    assert resolution["status"] == "resolved", f"Expected resolved, got {resolution['status']}"

    # --- Step 3: Enforce an action ---
    print("\n3. Enforcing a 'full rewrite' action...")
    enforcement = spec.enforce(
        action={"type": "code_change", "description": "Do a full rewrite of auth module"},
        scope=scope,
    )
    print(f"   Verdict: {enforcement['verdict']}")
    print(f"   Reason: {enforcement.get('reason', 'N/A')}")

    # --- Step 4: Inspect the binding set ---
    print(f"\n4. Inspecting binding set for scope '{scope}'...")
    binding = spec.inspect(scope=scope)
    print(f"   Active decisions: {len(binding)}")
    for dec in binding:
        print(f"   - {dec['title']} ({dec['id']})")

    # --- Step 5: Supersede the decision ---
    print(f"\n5. Superseding decision {dec_id}...")
    new_dec = spec.supersede(
        old_id=dec_id,
        new_title="Reject full rewrites (v2 — allow for test modules)",
        rationale="Updated: allow rewrites for test modules only.",
    )
    print(f"   New decision: {new_dec['id']} (status: {new_dec['status']})")
    assert new_dec["status"] == "active"

    # --- Verify final state ---
    print("\n6. Final binding set:")
    final_binding = spec.inspect(scope=scope)
    for dec in final_binding:
        print(f"   - {dec['title']} ({dec['id']}, status: {dec['status']})")

    # Cleanup
    shutil.rmtree(storage_dir, ignore_errors=True)

    print("\nAll steps completed successfully.")


if __name__ == "__main__":
    main()
