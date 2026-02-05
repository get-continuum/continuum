from __future__ import annotations

import json
from pathlib import Path

from continuum_local import load_semantics, resolve, to_semantic_contract


def main() -> None:
    doc = load_semantics(Path(__file__).parent.parent / "_shared" / "semantics.yaml")

    # Pretend these come from Slack context signals.
    context = {"team": "marketing", "surface": "slack"}
    query = "show spend"

    out = resolve(doc, query=query, context=context)
    print(json.dumps(out, indent=2, sort_keys=True))

    if out.get("status") == "resolved":
        contract = to_semantic_contract(out, context=context)
        print("\n--- semantic_contract ---")
        print(json.dumps(contract, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

