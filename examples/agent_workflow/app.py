from __future__ import annotations

import json
from pathlib import Path

from continuum_local import load_semantics, resolve, to_semantic_contract


def agent_step(doc: dict, *, query: str, context: dict) -> dict:
    """
    Stand-in for an agent tool call: resolve meaning, then emit a contract.
    """
    out = resolve(doc, query=query, context=context)
    if out.get("status") == "resolved":
        out["semantic_contract"] = to_semantic_contract(out, context=context)
    return out


def main() -> None:
    doc = load_semantics(Path(__file__).parent.parent / "_shared" / "semantics.yaml")

    contexts = [
        {"team": "finance", "surface": "agent"},
        {"team": "marketing", "surface": "agent"},
    ]
    queries = ["burn last week", "burn last week"]

    for ctx, q in zip(contexts, queries):
        out = agent_step(doc, query=q, context=ctx)
        print("\n=== step ===")
        print(json.dumps({"query": q, "context": ctx, "result": out}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

