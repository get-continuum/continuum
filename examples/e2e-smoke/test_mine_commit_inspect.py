"""E2E smoke test: mine → commit safe → inspect.

Run against a local Continuum API:
    python test_mine_commit_inspect.py
"""

from __future__ import annotations

import requests
import sys

API = "http://localhost:8787"

CONVERSATION = """
User: I'm planning a trip to Japan. Budget is $3000 max.
User: I'm vegetarian. No flying please, I prefer trains.
User: Always book hotels with free cancellation.
"""


def main() -> None:
    print("=== E2E: mine → commit → inspect ===\n")

    # Step 1: Mine
    print("1. Mining conversation...")
    resp = requests.post(f"{API}/mine", json={
        "conversations": [CONVERSATION],
        "scope_default": "user:e2e-test",
    })
    resp.raise_for_status()
    data = resp.json()

    facts = data.get("facts", [])
    candidates = data.get("decision_candidates", [])
    auto = data.get("auto_committed", [])

    print(f"   Facts: {len(facts)}")
    print(f"   Candidates: {len(candidates)}")
    print(f"   Auto-committed: {len(auto)}")
    assert len(facts) > 0, "Expected at least one fact"

    # Step 2: Commit remaining candidates
    print("\n2. Committing candidates...")
    committed_count = 0
    for cand in candidates:
        payload = cand.get("candidate_decision", {})
        resp = requests.post(f"{API}/commit", json={
            "title": payload.get("title", cand["title"]),
            "scope": payload.get("scope", "user:e2e-test"),
            "decision_type": payload.get("decision_type", "interpretation"),
            "rationale": payload.get("rationale", "E2E test"),
            "activate": True,
        })
        resp.raise_for_status()
        committed_count += 1
        print(f"   Committed: {cand['title']}")

    print(f"   Total committed: {committed_count}")

    # Step 3: Inspect
    print("\n3. Inspecting binding set...")
    resp = requests.get(f"{API}/inspect", params={"scope": "user:e2e-test"})
    resp.raise_for_status()
    data = resp.json()
    binding = data.get("binding", [])
    print(f"   Active decisions: {len(binding)}")
    for dec in binding:
        print(f"   - {dec.get('title', '?')} [{dec.get('status', '?')}]")

    assert len(binding) > 0, "Expected at least one active decision"

    print("\n=== PASS ===")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\n=== FAIL: {exc} ===")
        sys.exit(1)
