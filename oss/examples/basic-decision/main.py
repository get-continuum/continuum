#!/usr/bin/env python3
"""Basic Decision example for Continuum.

Demonstrates: commit -> get -> transition -> inspect.
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
            {"id": "opt_postgres", "title": "PostgreSQL", "selected": True},
            {
                "id": "opt_mongo",
                "title": "MongoDB",
                "selected": False,
                "rejected_reason": "No ACID guarantees",
            },
        ],
        rationale="Need ACID transactions for billing data.",
    )
    print(f"   Decision committed: {decision.id}\n")

    # 2. Get the decision by ID
    print("2. Getting decision...")
    loaded = client.get(decision.id)
    print(f"   Title: {loaded.title}")
    print(f"   Scope: {loaded.enforcement.scope}")
    print(f"   Status: {loaded.status}\n")

    # 3. Transition the decision to active
    print("3. Transitioning decision to active...")
    updated = client.update_status(decision.id, "active")
    print(f"   New status: {updated.status}\n")

    # 4. Inspect active decisions in scope
    print("4. Inspecting active decisions...")
    binding = client.inspect("repo:acme/backend")
    print(f"   Active decisions: {len(binding)}")
    for d in binding:
        print(f"     - {d['title']}")

    print("\nDone.")


if __name__ == "__main__":
    main()
