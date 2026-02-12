"""Deterministic conflict arbitration.

Given a list of competing decisions for a scope, select the winner using
a composite ranking that combines specificity, explicit precedence, authority,
and recency.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from continuum_precedence.specificity import enhanced_specificity
from continuum_precedence.authority import authority_rank


class ArbitrationResult(BaseModel):
    """Result of arbitrating among competing decisions."""

    winner: dict[str, Any]
    losers: list[dict[str, Any]]
    conflict_detected: bool
    scores: dict[str, float] = {}  # decision_id -> composite score


def _get_scope(decision: dict[str, Any]) -> str:
    enforcement = decision.get("enforcement")
    if isinstance(enforcement, dict):
        return str(enforcement.get("scope", ""))
    return str(decision.get("scope", ""))


def _explicit_precedence(decision: dict[str, Any]) -> int:
    enforcement = decision.get("enforcement")
    if isinstance(enforcement, dict):
        return int(enforcement.get("precedence") or 0)
    return 0


def _created_at(decision: dict[str, Any]) -> str:
    return str(decision.get("created_at") or "")


def _composite_score(decision: dict[str, Any]) -> float:
    """Compute a composite ranking score.

    Components (weighted):
      - Enhanced specificity (scope depth + type rank): weight 100
      - Explicit precedence field: weight 1000
      - Authority rank: weight 50
      - Recency (lexicographic ISO timestamp): tie-breaker
    """
    specificity = enhanced_specificity(_get_scope(decision))
    precedence = _explicit_precedence(decision)
    authority = authority_rank(decision)
    # We use precedence * 1000 so it's the strongest explicit signal,
    # then specificity * 1, then authority * 0.5
    return precedence * 1000.0 + specificity + authority * 0.5


def arbitrate(
    candidates: list[dict[str, Any]],
    scope: str | None = None,
) -> ArbitrationResult:
    """Select the winning decision from *candidates*.

    Parameters
    ----------
    candidates:
        List of decision dicts that all match a given scope.
    scope:
        Optional target scope (for context in the result).

    Returns
    -------
    ArbitrationResult
        Contains the winning decision, losers, and whether a real
        conflict was detected (more than one candidate).
    """
    if not candidates:
        return ArbitrationResult(
            winner={},
            losers=[],
            conflict_detected=False,
        )

    if len(candidates) == 1:
        return ArbitrationResult(
            winner=candidates[0],
            losers=[],
            conflict_detected=False,
            scores={candidates[0].get("id", ""): _composite_score(candidates[0])},
        )

    # Score all candidates
    scored = [(c, _composite_score(c)) for c in candidates]

    # Sort by composite score desc, then recency desc (for tie-breaking)
    scored.sort(key=lambda x: (x[1], _created_at(x[0])), reverse=True)

    scores = {c.get("id", ""): s for c, s in scored}
    winner = scored[0][0]
    losers = [c for c, _ in scored[1:]]

    return ArbitrationResult(
        winner=winner,
        losers=losers,
        conflict_detected=True,
        scores=scores,
    )
