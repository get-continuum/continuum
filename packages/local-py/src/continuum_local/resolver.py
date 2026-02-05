from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml

SemanticsDoc = Dict[str, Any]


@dataclass(frozen=True)
class Candidate:
    metric_id: str
    canonical_name: str
    description: str
    tags: Tuple[str, ...] = ()


def load_semantics(path: Union[str, Path]) -> SemanticsDoc:
    """
    Load a tiny YAML/JSON semantics file.

    Expected shape (minimal):
      metrics:
        - metric_id: revenue
          canonical_name: Revenue
          description: Net revenue excluding refunds
          tags: [finance, marketing]
    """
    p = Path(path)
    raw = p.read_text(encoding="utf-8")
    if p.suffix.lower() in {".json"}:
        doc = json.loads(raw)
    else:
        doc = yaml.safe_load(raw)
    if not isinstance(doc, dict):
        raise ValueError("semantics file must be an object")
    return doc


def _candidates(doc: SemanticsDoc) -> List[Candidate]:
    out: List[Candidate] = []
    for m in (doc.get("metrics") or []):
        if not isinstance(m, dict):
            continue
        metric_id = str(m.get("metric_id") or "").strip()
        if not metric_id:
            continue
        canonical_name = str(m.get("canonical_name") or metric_id)
        description = str(m.get("description") or canonical_name)
        tags = tuple(str(t) for t in (m.get("tags") or []) if str(t).strip())
        out.append(Candidate(metric_id=metric_id, canonical_name=canonical_name, description=description, tags=tags))
    return out


def resolve(doc: SemanticsDoc, *, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Deterministic, no-ML resolver.

    Rules:
    - normalize query to tokens
    - score candidates by substring/token overlap
    - boost if context['team'] matches candidate tag
    - return {status: resolved|ambiguous|no_match}
    """
    q = (query or "").strip().lower()
    ctx = context or {}
    team = str(ctx.get("team") or "").strip().lower()

    cands = _candidates(doc)
    if not q or not cands:
        return {"status": "no_match", "reason": "empty query or no candidates"}

    tokens = [t for t in q.replace("/", " ").replace("_", " ").split() if t]

    scored: List[Tuple[float, Candidate]] = []
    for c in cands:
        hay = " ".join([c.metric_id, c.canonical_name, c.description]).lower()
        score = 0.0
        if q in hay:
            score += 2.0
        for t in tokens:
            if t in hay:
                score += 1.0
        if team and team in {t.lower() for t in c.tags}:
            score += 1.5
        scored.append((score, c))

    scored.sort(key=lambda x: (-x[0], x[1].metric_id))
    best_score = scored[0][0]
    if best_score <= 0:
        return {"status": "no_match", "reason": "no overlap with any metric"}

    top = [c for s, c in scored if s == best_score]
    if len(top) == 1:
        return {
            "status": "resolved",
            "resolved_metric": {
                "metric_id": top[0].metric_id,
                "canonical_name": top[0].canonical_name,
                "description": top[0].description,
            },
            "confidence": min(1.0, 0.6 + 0.1 * best_score),
            "reason": "deterministic match",
        }

    candidates = top[:5]
    return {
        "status": "ambiguous",
        "candidates": [
            {"metric_id": c.metric_id, "canonical_name": c.canonical_name, "description": c.description}
            for c in candidates
        ],
        "confidence": 0.55,
        "reason": "multiple metrics match equally well",
    }


def to_semantic_contract(resolution: Dict[str, Any], *, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Convert a resolved metric into a minimal, stable 'SemanticContract' dict.
    """
    ctx = context or {}
    if resolution.get("status") != "resolved":
        raise ValueError("resolution must be status=resolved to build a contract")

    m = resolution.get("resolved_metric") or {}
    metric_id = m.get("metric_id")
    definition = {"display": m.get("canonical_name") or metric_id, "description": m.get("description") or ""}
    return {
        "identity": {"metric_id": metric_id},
        "definition": definition,
        "context": ctx,
        "source": {"system": "continuum_local"},
    }

