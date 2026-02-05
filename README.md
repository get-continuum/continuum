# Continuum

Shared semantic state for AI agents.

Continuum helps agents, copilots, and workflows agree on what things mean — across users, tools, and time.

AI systems don’t fail because they forget.  
They fail because they disagree on meaning.

Continuum resolves meaning before execution, so agents stay correct.

## Why Continuum?

Most AI stacks rely on:

- prompts to encode meaning
- RAG to retrieve context
- memory to recall history

None of these decide **which definition is correct** when ambiguity exists.

Continuum introduces a missing primitive:

**Semantic resolution — shared, stable meaning for AI agents.**

## What Continuum does

- Resolves ambiguous terms like revenue, bookings, users
- Anchors meaning to stable semantic IDs
- Returns grounded semantic contracts, not guesses
- Keeps multiple agents aligned over time
- Works across chat, analytics, and workflows

## What Continuum is not

- **Not RAG** (it doesn’t retrieve text)
- **Not chat memory** (it doesn’t store conversations)
- **Not a semantic layer replacement**
- **Not an agent framework**

Continuum is a semantic state layer.

## Quickstart (TypeScript SDK)

Install:

```bash
npm install @get-continuum/sdk
```

Resolve meaning in a few lines of code:

```ts
import { Continuum } from "@get-continuum/sdk";

const continuum = new Continuum({
  baseUrl: process.env.CONTINUUM_BASE_URL, // e.g. https://api.getcontinuum.ai
  workspaceId: "default",
  apiKey: process.env.CONTINUUM_API_KEY,
});

const intent = await continuum.resolve({
  query: "What is revenue?",
  context: { team: "finance" },
});

console.log(intent.resolved_metric);
```

What you get back:

- `intent.resolved_metric.metric_id` — stable semantic ID
- `intent.resolved_metric.description` — resolved meaning
- `intent.confidence` — resolution confidence
- `intent.reason` — why Continuum chose that meaning

Continuum returns semantic **contracts**, not free-text answers.

## Local usage (Python, no backend required)

Continuum includes a local resolver for development and testing.

Install:

```bash
pip install continuum-local
```

Run the CLI:

```bash
continuum-local resolve --semantics examples/_shared/semantics.yaml --query "revenue" --context '{"team":"finance"}'
```

Or use it as a library:

```python
from continuum_local import load_semantics, resolve, to_semantic_contract

doc = load_semantics("examples/_shared/semantics.yaml")
out = resolve(doc, query="revenue", context={"team": "finance"})

if out.get("status") == "resolved":
    contract = to_semantic_contract(out, context={"team": "finance"})
    print(contract)
```

This lets you:

- try Continuum in minutes
- run examples locally
- understand the API surface
- contribute without infra access

## Examples

See `examples/` for:

- `examples/slack_copilot`: Slack copilot-style loop (local)
- `examples/agent_workflow`: multi-step “agent” loop (local)

## How it fits in the AI stack

```text
Agent / Copilot
 ├─ Memory (preferences, history)
 ├─ Continuum (semantic resolution)
 └─ LLM + tools
```

Memory remembers context.  
Continuum decides meaning.

## Open source vs core

This repository contains:

- SDKs
- semantic contract types
- local resolver
- examples

The Continuum core engine (semantic graph, versioning, drift detection, multi-tenant infra) lives in a separate repository and is source-available.

This repo is the on-ramp, not the engine.

## Roadmap

- TypeScript SDK (this repo)
- Python local resolver (this repo)
- 2 examples (this repo)
- Python SDK (hosted client) (v1.1)

## Contributing

Issues and PRs welcome.

Good first contributions:

- examples
- local resolver improvements
- SDK ergonomics
- docs

## License

Apache 2.0 (OSS components).

## Learn more

- **Website**: `https://getcontinuum.ai`
- **Docs**: `https://docs.getcontinuum.ai`
- **Core engine**: `https://github.com/get-continuum/continuum-core`
