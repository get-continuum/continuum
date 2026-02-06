# Continuum Local (Python)

Local (no-backend) semantic resolver for demos/tests.

## Install

```bash
pip install continuum-local
```

## CLI

```bash
# Create a minimal semantics file
cat > semantics.yaml <<'EOF'
metrics:
  - metric_id: revenue
    canonical_name: Revenue
    description: Net revenue
    tags: [marketing]
EOF

continuum-local resolve --semantics semantics.yaml --query "revenue" --context '{"team":"marketing"}'
```

## Library

```python
from continuum_local import load_semantics, resolve, to_semantic_contract

doc = load_semantics("semantics.yaml")
out = resolve(doc, query="revenue", context={"team": "marketing"})
print(out)

if out.get("status") == "resolved":
    print(to_semantic_contract(out, context={"team": "marketing"}))
```

