# Continuum Local (Python)

Local (no-backend) semantic resolver for demos/tests.

## Install

```bash
pip install continuum-local
```

## CLI

```bash
continuum-local resolve --semantics demo/semantics.yaml --query "revenue" --context '{"team":"marketing"}'
```

## Library

```python
from continuum_local import load_semantics, resolve, to_semantic_contract

doc = load_semantics("demo/semantics.yaml")
out = resolve(doc, query="revenue", context={"team": "marketing"})
print(out)

if out.get("status") == "resolved":
    print(to_semantic_contract(out, context={"team": "marketing"}))
```

