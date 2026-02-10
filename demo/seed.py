#!/usr/bin/env python3
"""Seed the Continuum demo store with example decisions.

Can run standalone against the API or directly via the SDK.
"""

from __future__ import annotations

import json
import os
import sys
import time

DEMO_DECISIONS = [
    {
        "title": "Reject full rewrites",
        "scope": "repo:demo",
        "decision_type": "rejection",
        "rationale": "Full rewrites carry too much risk. Prefer incremental refactors.",
        "options": [
            {"title": "Incremental refactor", "selected": True},
            {"title": "Full rewrite", "selected": False, "rejected_reason": "Too risky"},
        ],
        "activate": True,
    },
    {
        "title": "production-ready means tests + error handling",
        "scope": "repo:demo",
        "decision_type": "interpretation",
        "rationale": "Ambiguous term resolved: production-ready requires test coverage and structured error handling.",
        "activate": True,
    },
    {
        "title": "Confirm before API-breaking changes",
        "scope": "repo:demo",
        "decision_type": "behavior_rule",
        "rationale": "Any change that modifies a public API contract must be confirmed before proceeding.",
        "activate": True,
    },
]


def seed_via_api(base_url: str) -> None:
    """Seed decisions by POSTing to the demo API."""
    import urllib.request

    for dec in DEMO_DECISIONS:
        req = urllib.request.Request(
            f"{base_url}/commit",
            data=json.dumps(dec).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read())
                print(f"  Seeded: {result['decision']['title']} ({result['decision']['id']})")
        except Exception as exc:
            print(f"  Failed to seed '{dec['title']}': {exc}", file=sys.stderr)

    print("Seeding complete.")


def seed_via_sdk(storage_dir: str | None = None) -> None:
    """Seed decisions directly via the Continuum SDK."""
    from continuum.client import ContinuumClient

    client = ContinuumClient(storage_dir=storage_dir)

    for dec_data in DEMO_DECISIONS:
        activate = dec_data.pop("activate", False)
        dec = client.commit(**dec_data)
        if activate:
            client.update_status(dec.id, "active")
        print(f"  Seeded: {dec.title} ({dec.id})")

    print("Seeding complete.")


def main() -> None:
    api_url = os.environ.get("DEMO_API_URL")
    store_dir = os.environ.get("CONTINUUM_STORE")

    print("Continuum Demo — Seeding decisions...")

    if api_url:
        # Wait a moment for API readiness
        time.sleep(2)
        seed_via_api(api_url)
    elif store_dir:
        seed_via_sdk(store_dir)
    else:
        seed_via_sdk()


if __name__ == "__main__":
    main()
