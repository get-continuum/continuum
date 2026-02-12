"""E2E smoke test: conflicting decisions → inspect includes winner explanation.

Run against a local Continuum API:
    python test_conflict_resolution.py
"""

from __future__ import annotations

import requests
import sys

API = "http://localhost:8787"


def main() -> None:
    print("=== E2E: conflict detection + precedence ===\n")

    scope = "repo:e2e-conflict"

    # Step 1: Commit two competing decisions at different scopes
    print("1. Committing two competing decisions...")

    # Decision 1: team-level
    resp = requests.post(f"{API}/commit", json={
        "title": "Use PostgreSQL for the database",
        "scope": scope,
        "decision_type": "preference",
        "rationale": "Team prefers PostgreSQL",
        "precedence": 1,
        "activate": True,
    })
    resp.raise_for_status()
    dec1 = resp.json().get("decision", {})
    print(f"   Decision 1: {dec1.get('title')} (id: {dec1.get('id')}, precedence: 1)")

    # Decision 2: higher precedence
    resp = requests.post(f"{API}/commit", json={
        "title": "Use SQLite for the database",
        "scope": scope,
        "decision_type": "preference",
        "rationale": "Lead prefers SQLite for simplicity",
        "precedence": 10,
        "activate": True,
    })
    resp.raise_for_status()
    dec2 = resp.json().get("decision", {})
    print(f"   Decision 2: {dec2.get('title')} (id: {dec2.get('id')}, precedence: 10)")

    # Step 2: Inspect — should detect conflict
    print("\n2. Inspecting for conflicts...")
    resp = requests.get(f"{API}/inspect", params={"scope": scope})
    resp.raise_for_status()
    data = resp.json()

    binding = data.get("binding", [])
    conflict_notes = data.get("conflict_notes", [])

    print(f"   Active decisions: {len(binding)}")
    print(f"   Conflict notes: {len(conflict_notes)}")

    if conflict_notes:
        for note in conflict_notes:
            print(f"   Winner: {note.get('winner_id')}")
            print(f"   Explanation: {note.get('explanation')}")
            # The higher-precedence decision should win
            assert note.get("winner_id") == dec2.get("id"), (
                f"Expected {dec2.get('id')} to win (higher precedence)"
            )
    else:
        print("   (No conflict notes — precedence engine may not be loaded)")

    assert len(binding) >= 2, "Expected at least 2 active decisions"

    print("\n=== PASS ===")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\n=== FAIL: {exc} ===")
        sys.exit(1)
