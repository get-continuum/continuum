"""E2E smoke test: resolve(ambiguous) → commit_from_clarification → enforce.

Run against a local Continuum API:
    python test_clarification_flow.py
"""

from __future__ import annotations

import requests
import sys

API = "http://localhost:8787"


def main() -> None:
    print("=== E2E: resolve → clarify → commit → enforce ===\n")

    scope = "team:e2e-clarify"

    # Step 1: Resolve an ambiguous query (no prior decisions)
    print("1. Resolving ambiguous query...")
    resp = requests.post(f"{API}/resolve", json={
        "prompt": "what authentication method should we use?",
        "scope": scope,
        "candidates": [
            {"id": "opt_jwt", "title": "JWT tokens"},
            {"id": "opt_session", "title": "Session cookies"},
        ],
    })
    resp.raise_for_status()
    data = resp.json()
    resolution = data.get("resolution", {})

    print(f"   Status: {resolution.get('status')}")
    assert resolution.get("status") == "needs_clarification", "Expected needs_clarification"

    clarification = resolution.get("clarification", {})
    print(f"   Question: {clarification.get('question')}")
    print(f"   Candidates: {len(clarification.get('candidates', []))}")

    # Step 2: Commit from clarification
    print("\n2. Committing from clarification (JWT tokens)...")
    resp = requests.post(f"{API}/commit_from_clarification", json={
        "chosen_option_id": "opt_jwt",
        "scope": scope,
        "title": "Use JWT tokens for authentication",
        "rationale": "E2E test: selected JWT",
    })
    resp.raise_for_status()
    data = resp.json()
    dec = data.get("decision", {})
    print(f"   Decision: {dec.get('title')} ({dec.get('id')})")
    assert dec.get("status") == "active", "Expected active decision"

    # Step 3: Resolve again — should be resolved now
    print("\n3. Re-resolving same query...")
    resp = requests.post(f"{API}/resolve", json={
        "prompt": "Use JWT tokens for authentication",
        "scope": scope,
    })
    resp.raise_for_status()
    data = resp.json()
    resolution2 = data.get("resolution", {})
    print(f"   Status: {resolution2.get('status')}")
    assert resolution2.get("status") == "resolved", "Expected resolved"

    # Step 4: Enforce an action
    print("\n4. Enforcing action...")
    resp = requests.post(f"{API}/enforce", json={
        "scope": scope,
        "action": {
            "type": "code_change",
            "description": "Implement authentication with session cookies",
        },
    })
    resp.raise_for_status()
    data = resp.json()
    enforcement = data.get("enforcement", {})
    print(f"   Verdict: {enforcement.get('verdict')}")
    print(f"   Reason: {enforcement.get('reason')}")

    print("\n=== PASS ===")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\n=== FAIL: {exc} ===")
        sys.exit(1)
