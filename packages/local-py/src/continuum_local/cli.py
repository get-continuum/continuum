from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from .resolver import load_semantics, resolve, to_semantic_contract


def _json_arg(raw: str) -> Dict[str, Any]:
    raw = (raw or "").strip()
    if not raw:
        return {}
    obj = json.loads(raw)
    if not isinstance(obj, dict):
        raise ValueError("context must be a JSON object")
    return obj


def main() -> None:
    p = argparse.ArgumentParser(prog="continuum-local")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("resolve", help="Resolve query against local semantics")
    r.add_argument("--semantics", required=True, help="YAML/JSON semantics file path")
    r.add_argument("--query", required=True, help="Natural language query")
    r.add_argument("--context", default="{}", help="JSON object (e.g. '{\"team\":\"marketing\"}')")

    args = p.parse_args()
    if args.cmd == "resolve":
        doc = load_semantics(args.semantics)
        ctx = _json_arg(args.context)
        out = resolve(doc, query=args.query, context=ctx)
        print(json.dumps(out, indent=2, sort_keys=True))
        if out.get("status") == "resolved":
            contract = to_semantic_contract(out, context=ctx)
            print("\n--- semantic_contract ---")
            print(json.dumps(contract, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

