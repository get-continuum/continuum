# Getting Started

This guide walks you through installing Continuum and making your first decision.

## Prerequisites

- Python 3.10 or later
- pip

## Installation

### OSS-only (Apache-2.0)

```bash
pip install -e oss/sdk/python
```

### With Engine (requires Core license)

```bash
pip install -e oss/sdk/python
pip install -e core/
```

## Create a Decision

```python
from continuum import ContinuumClient

client = ContinuumClient()

decision = client.commit(
    title="Use PostgreSQL for user store",
    scope="repo:acme/backend",
    decision_type="rejection",
    options=[
        {"title": "PostgreSQL", "selected": True},
        {"title": "MongoDB", "selected": False, "rejected_reason": "No ACID"},
    ],
    rationale="Need ACID transactions for billing data.",
)

print(f"Decision committed: {decision.id}")
```

## Inspect a Decision

```python
result = client.inspect(decision.id)
print(result)
```

The `inspect` call returns the full decision record including title, options, rationale, scope, and current lifecycle status.

## Enforce a Decision

```python
from continuum.enforce import enforce

verdict = enforce(
    decision=decision,
    action_context={"agent": "coding-agent", "action": "create_table"},
)

print(f"Verdict: {verdict.outcome}")  # allow | confirm | block
```

Enforcement is deterministic: given the same decision and action context, you always get the same verdict.

## With Engine (Advanced)

If you have the Core engine installed, resolution and enforcement gain LLM-backed intelligence:

```python
from continuum import ContinuumClient

# The client auto-discovers engine hooks when core/ is installed
client = ContinuumClient()

# Resolve checks if a prior decision covers this prompt
resolution = client.resolve(
    prompt="What database should we use for the user service?",
    scope="repo:acme/backend",
)

if resolution.status == "resolved":
    print(f"Found prior decision: {resolution.decision.title}")
else:
    print("No prior decision found — needs clarification.")
```

## Next Steps

- Read the [Architecture overview](architecture.md) for deeper context
- Explore the [OSS Boundary](oss-boundary.md) to understand what lives where
- Try the [flagship demo cookbook](cookbooks/flagship-demo.md) for an end-to-end walkthrough
