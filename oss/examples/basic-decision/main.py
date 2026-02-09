#!/usr/bin/env python3
"""Basic Decision example for Continuum.

Demonstrates: commit -> inspect -> transition.
"""

from __future__ import annotations

from continuum import ContinuumClient


def main() -> None:
    print("=== Continuum Basic Decision Example ===\n")

    client = ContinuumClient()

    # 1. Commit a decision
    print("1. Committing decision...")
    decision = client.commit(
        title="Use PostgreSQL for user store",
        scope="repo:acme/backend",
        decision_type="rejection",
        options=[
            {"title": "PostgreSQL", "selected": True},
            {
                "title": "MongoDB",
                "selected": False,
                "rejected_reason": "No ACID guarantees",
            },
        ],
        rationale="Need ACID transactions for billing data.",
    )
    print(f"   Decision committed: {decision.id}\n")

    # 2. Inspect the decision
    print("2. Inspecting decision...")
    inspected = client.inspect(decision.id)
    print(f"   Title: {inspected.title}")
    print(f"   Scope: {inspected.scope}")
    print(f"   Status: {inspected.status}\n")

    # 3. Transition the decision
    print("3. Transitioning decision...")
    updated = client.transition(decision.id, to="active")
    print(f"   New status: {updated.status}\n")

    print("Done.")


if __name__ == "__main__":
    main()
