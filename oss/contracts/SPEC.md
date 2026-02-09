# Continuum Contracts Specification v0.1

> **Status**: Draft  
> **Schema Version**: 0.1.0  
> **Last Updated**: 2025-02-08

## 1. Introduction

The Contracts specification defines the structure, lifecycle, and enforcement rules for **Decisions** in the Continuum platform. Decisions are the atomic unit of institutional knowledge — each one captures a choice that was made, the reasoning behind it, what alternatives were considered, and how the decision should be enforced going forward.

## 2. Decision Fields

### 2.1 Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Unique identifier. Must match pattern `dec_[a-zA-Z0-9]+`. |
| `version` | `integer` | Version number, starting at 0. Must be >= 0. |
| `status` | `string` | Current lifecycle status. One of: `draft`, `active`, `superseded`, `archived`. |
| `title` | `string` | Human-readable title describing the decision. |
| `created_at` | `string` (date-time) | ISO 8601 timestamp of when the decision was created. |
| `updated_at` | `string` (date-time) | ISO 8601 timestamp of when the decision was last updated. |

### 2.2 Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `rationale` | `string` | Explanation of why this decision was made. |
| `stakeholders` | `array[string]` | List of people or teams involved in the decision. |
| `metadata` | `object` | Arbitrary key-value metadata. |

### 2.3 Options Considered

The `options_considered` field is an array of option objects:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `string` | Yes | Unique option identifier. Must match pattern `opt_[a-zA-Z0-9]+`. |
| `title` | `string` | Yes | Description of the option. |
| `selected` | `boolean` | Yes | Whether this option was chosen. |
| `rejected_reason` | `string` | No | Reason this option was rejected (if applicable). |

### 2.4 Context

The `context` object provides information about what triggered the decision:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `trigger` | `string` | Yes | What triggered this decision (e.g., "code_review", "architecture_discussion"). |
| `source` | `string` | Yes | Where the decision originated (e.g., "pull_request", "slack_thread"). |
| `timestamp` | `string` (date-time) | Yes | When the triggering event occurred. |
| `actor` | `string` | No | Who or what triggered the decision. |

Additional properties are allowed on the context object to support extension.

### 2.5 Enforcement Fields

| Field | Type | Description |
|-------|------|-------------|
| `scope` | `string` | Where this decision applies. See [Section 5](#5-scope-types). |
| `decision_type` | `string` | Category of decision. See [Section 6](#6-decision-types). |
| `supersedes` | `string` (optional) | ID of the decision this one replaces. Must match pattern `dec_*`. |
| `precedence` | `integer` (optional) | Priority level for conflict resolution. Higher values take precedence. |
| `override_policy` | `string` | What happens when a rejected option is encountered. Default: `invalid_by_default`. |

## 3. Lifecycle States

Decisions follow a strict lifecycle with four states:

```
┌───────┐     ┌────────┐     ┌─────────────┐     ┌──────────┐
│ draft │────▶│ active │────▶│ superseded  │────▶│ archived │
└───────┘     └────────┘     └─────────────┘     └──────────┘
                  │                                     ▲
                  └─────────────────────────────────────┘
```

### 3.1 State Descriptions

- **`draft`**: The decision is being authored and is not yet in effect. All fields are mutable.
- **`active`**: The decision is in effect and being enforced. Core fields become immutable.
- **`superseded`**: The decision has been replaced by a newer decision. The `supersedes` field on the replacement links back to this decision.
- **`archived`**: The decision is no longer relevant and is retained for historical purposes only.

### 3.2 Valid Transitions

| From | To | Description |
|------|----|-------------|
| `draft` | `active` | Decision is approved and takes effect. |
| `active` | `superseded` | A new decision replaces this one. |
| `active` | `archived` | Decision is retired without replacement. |
| `superseded` | `archived` | Superseded decision is archived for cleanup. |

**Invalid transitions** (these MUST be rejected):

- `active` → `draft` (cannot un-activate)
- `superseded` → `active` (cannot re-activate a superseded decision)
- `superseded` → `draft` (cannot revert to draft)
- `archived` → any state (archived is terminal)
- `draft` → `superseded` (must be active first)
- `draft` → `archived` (must be active first)

## 4. Immutability Guarantees

Once a decision transitions to `active` status, the following **core fields become immutable** and MUST NOT be modified:

- `id`
- `title`
- `options_considered`
- `context`
- `decision_type`
- `scope`

Fields that MAY still be updated after activation:

- `status` (only valid forward transitions)
- `updated_at` (automatically updated)
- `metadata` (for annotations and tagging)
- `version` (incremented on any allowed change)

## 5. Scope Types

The `scope` field defines where a decision applies. It uses a prefix-based format:

| Scope Prefix | Example | Description |
|-------------|---------|-------------|
| `repo:` | `repo:acme/backend` | Applies to a specific repository. |
| `folder:` | `folder:src/api/auth` | Applies to a specific folder path. |
| `user:` | `user:alice` | Applies to a specific user's work. |
| `workflow:` | `workflow:ci/deploy` | Applies to a specific workflow or pipeline. |
| `team:` | `team:finance` | Applies to a specific team. |

Scopes are hierarchical — a `repo:` scope is broader than a `folder:` scope within that repo. When decisions conflict, the more specific scope takes precedence unless `precedence` values indicate otherwise.

## 6. Decision Types

| Type | Description | Example |
|------|-------------|---------|
| `interpretation` | Defines how an ambiguous term or concept should be understood. | "Revenue means net revenue excluding refunds." |
| `rejection` | Explicitly rejects an option, tool, or approach. | "Do not use MongoDB for this project." |
| `preference` | Expresses a preferred choice among valid alternatives. | "Prefer PostgreSQL over MySQL for new services." |
| `behavior_rule` | Defines a behavioral constraint or rule for agents/workflows. | "Always run linting before committing." |

## 7. Precedence and Supersession

### 7.1 Precedence

When multiple active decisions could apply to the same context, conflicts are resolved by:

1. **Scope specificity**: More specific scopes win (e.g., `folder:` > `repo:`).
2. **Precedence value**: Higher `precedence` integer wins among same-scope decisions.
3. **Recency**: If precedence values are equal, the most recently activated decision wins (by `created_at`).

### 7.2 Supersession

A decision can explicitly supersede another by setting the `supersedes` field to the ID of the older decision. When this happens:

1. The old decision's status transitions to `superseded`.
2. The new decision becomes the authoritative source.
3. The old decision is retained for audit history.

## 8. Override Policy

The `override_policy` field controls what happens when a user or agent attempts to use a rejected option:

| Policy | Behavior |
|--------|----------|
| `invalid_by_default` | The rejected option is treated as invalid. Any attempt to use it is blocked or flagged as an error. This is the default. |
| `warn` | The rejected option is allowed but generates a warning that the decision recommends against it. |
| `allow` | The decision is informational only. Rejected options are allowed without restriction. |

**Default behavior**: If `override_policy` is not specified, it defaults to `invalid_by_default`. This means rejected options are blocked unless explicitly overridden.

## 9. Schema Versioning

- The current schema version is `0.1.0`.
- Schemas follow [Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`.
- Breaking changes increment the MAJOR version.
- New optional fields increment the MINOR version.
- Bug fixes and clarifications increment the PATCH version.
- The `schema_version` field in each schema tracks compatibility.
