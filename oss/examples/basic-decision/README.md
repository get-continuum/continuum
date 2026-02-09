# Example: Basic Decision

This example demonstrates the core Continuum workflow: **commit** a decision, **inspect** it, and **transition** its lifecycle state.

## What it does

1. Creates a `ContinuumClient` instance.
2. Commits a sample decision ("Use PostgreSQL for user store") with options and rationale.
3. Inspects the committed decision to view its full record.
4. Transitions the decision through its lifecycle.
5. Prints results at each step.

## Running

```bash
# From the repository root
pip install -e oss/sdk/python
python oss/examples/basic-decision/main.py
```

## Expected output

```
=== Continuum Basic Decision Example ===

1. Committing decision...
   Decision committed: <decision-id>

2. Inspecting decision...
   Title: Use PostgreSQL for user store
   Scope: repo:acme/backend
   Status: committed

3. Transitioning decision...
   New status: active

Done.
```
