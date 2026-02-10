# @get-continuum/sdk

TypeScript SDK for the [Continuum](https://getcontinuum.ai) decision control plane.

## Install

```bash
npm install @get-continuum/sdk
```

## Quick start

```ts
import { ContinuumClient } from "@get-continuum/sdk";

const client = new ContinuumClient({
  baseUrl: "http://localhost:8000",
});

// Commit a decision
const decision = await client.commit({
  title: "Revenue means net_revenue",
  scope: "org:acme",
  decision_type: "interpretation",
  rationale: "Finance team confirmed net_revenue is the standard metric.",
});

// Inspect active decisions
const bindings = await client.inspect("org:acme");

// Resolve ambiguity
const result = await client.resolve({
  query: "What is revenue?",
  scope: "org:acme",
});

// Enforce an action
const enforcement = await client.enforce({
  action: {
    type: "code_change",
    description: "Change revenue metric to gross_revenue",
    scope: "org:acme",
  },
  scope: "org:acme",
});
```

## API

### `ContinuumClient`

| Method | Description |
|---|---|
| `commit(params)` | Create and persist a new decision |
| `get(id)` | Get a decision by ID |
| `inspect(scope)` | List active decisions for a scope |
| `resolve(params)` | Run the ambiguity gate |
| `enforce(params)` | Evaluate an action against decisions |
| `supersede(params)` | Replace an existing decision |
| `health()` | Health check |

### Options

```ts
const client = new ContinuumClient({
  baseUrl: "https://api.getcontinuum.ai",
  apiKey: "ck_...",
  timeout: 30_000,
});
```

## Types

All types are exported for use in your application:

```ts
import type { Decision, DecisionType, ResolveResult } from "@get-continuum/sdk";
```

## License

Apache-2.0
