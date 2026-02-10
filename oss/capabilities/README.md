# continuum-capabilities

A-la-carte capability registry and configuration loader for Continuum.

## Overview

This module lets you toggle Continuum features per environment without rewriting code. Define what's active in a `continuum.yaml` file.

## Modes

| Mode | Capabilities enabled |
|---|---|
| `local` | store, engine, mcp, cli |
| `hosted` | store, engine, api, auth |
| `demo` | store, engine, ambiguity_gate, inspector |

## Usage

```python
from continuum_capabilities import load_config, CapabilityRegistry
from continuum_capabilities.loader import apply_config

# Load from continuum.yaml (or defaults)
config = load_config()

# Apply to a registry
registry = apply_config(config)

# Check what's active
print(registry.list_enabled())  # ["store", "engine", "mcp", "cli"]
print(registry.is_enabled("auth"))  # False
```

## Configuration

Copy `continuum.example.yaml` to `./continuum.yaml`:

```yaml
version: "0.1"
mode: local
store:
  backend: file
  path: .continuum
adapters:
  model: null
  orchestrator: null
  memory: null
```

## Adapter interfaces

Extend Continuum with custom integrations by implementing:

- `ModelAdapter` — LLM model integration (OpenAI, Anthropic, etc.)
- `OrchestratorAdapter` — Workflow framework integration (LangGraph, CrewAI)
- `MemorySignalSource` — Memory/context signal source (mem0, Zep, SQLite)

```python
from continuum_capabilities.adapters import ModelAdapter

class MyModelAdapter(ModelAdapter):
    async def complete(self, prompt: str, **kwargs) -> str:
        ...
    async def embed(self, text: str) -> list[float]:
        ...
```

## License

Apache-2.0
