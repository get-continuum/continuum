# Code Pack

Decision templates for code-related workflows: rejection, confirmation, interpretation.

## Templates

| Template | File | Purpose |
|----------|------|---------|
| **Reject Option** | [`templates/reject-option.json`](templates/reject-option.json) | Record that a specific approach was evaluated and rejected. The enforcement engine will **block** actions matching the rejected option. |
| **Confirm Before** | [`templates/confirm-before.json`](templates/confirm-before.json) | Require explicit confirmation before proceeding with a sensitive action (e.g. migration, API break). The enforcement engine will return a **confirm** verdict. |
| **Interpretation** | [`templates/interpretation.json`](templates/interpretation.json) | Record how an ambiguous term or concept was interpreted. Future queries matching the scope will resolve against this decision instead of re-asking. |

## Usage

1. Copy the desired template into your project's decisions directory.
2. Replace all `<...>` placeholders with concrete values.
3. Validate against the [decision schema](../../contracts/schemas/decision.v0.schema.json).
4. The Continuum enforcement engine and resolve gate will automatically pick up active decisions.

## Field Reference

- **scope** — Hierarchical path (e.g. `project/backend/api`) used for matching.
- **decision_type** — One of `rejection`, `preference`, `interpretation`, `behavior_rule`.
- **override_policy** — `invalid_by_default` (block overrides), `warn`, or `allow`.
- **status** — Must be `active` for the decision to be enforced. Use `archived` to disable.
