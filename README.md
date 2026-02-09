# Continuum

**Decision Control Plane for AI Agents**

Continuum captures, enforces, and resolves decisions so AI agents behave consistently across prompts, sessions, and teams.

## Repository layout

```
oss/            Open-source layer (Apache-2.0)
  contracts/    Decision JSON Schemas, spec, examples
  sdk/python/   Python SDK (deterministic)
  cli/          CLI inspector (typer-based)
  packs/code/   Decision templates for code workflows
  mcp-server/   MCP server exposing decision tools
  integrations/ LangGraph, LlamaIndex adapters
  examples/     Runnable examples
  docs/         Documentation

core/           Engine implementations (BSL-1.1)
  src/          Scorers, compiler, policies, resolution, LLM layer
  tests/        Tests with mocked LLM responses
```

## Quick start

```bash
pip install continuum-sdk
```

```python
from continuum import ContinuumClient

client = ContinuumClient()
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
            "rejected_reason": "No ACID",
        },
    ],
    rationale="Need ACID transactions for billing data.",
)
```

Run the flagship demo:

```bash
python examples/flagship-demo/flagship_demo.py
```

## OSS boundary

The `oss/` layer ships deterministic logic only: schema validation, lifecycle state machine, rule-based enforcement, and abstract hooks for extension.

Heuristic implementations (ambiguity scoring, decision compilation, risk scoring, LLM integration) live in `core/` under a BSL license. See [BOUNDARY.md](BOUNDARY.md).

## License

- `oss/`: [Apache-2.0](LICENSE)
- `core/`: [BSL-1.1](core/LICENSE)
