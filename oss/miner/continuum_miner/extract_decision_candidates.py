"""Map extracted facts to decision candidates.

Each fact becomes a :class:`DecisionCandidate` with a pre-filled decision
contract, scope suggestion, risk level, and confidence.  The mapping is
deterministic and rules-based.
"""

from __future__ import annotations

from typing import Optional
from uuid import uuid4

from continuum_miner.types import (
    DecisionCandidate,
    Fact,
    RiskLevel,
)

# ---------------------------------------------------------------------------
# Category → decision_type + risk mapping
# ---------------------------------------------------------------------------

_CATEGORY_MAP: dict[str, tuple[str, RiskLevel]] = {
    "preference": ("preference", RiskLevel.low),
    "constraint": ("behavior_rule", RiskLevel.low),
    "rejection": ("rejection", RiskLevel.medium),
    "interpretation": ("interpretation", RiskLevel.medium),
    "behavior_rule": ("behavior_rule", RiskLevel.low),
}


def extract_decision_candidates(
    facts: list[Fact],
    scope_default: str,
    semantic_refs: Optional[list[str]] = None,
) -> list[DecisionCandidate]:
    """Convert extracted facts into decision candidates.

    Parameters
    ----------
    facts:
        Facts output from :func:`extract_facts`.
    scope_default:
        Default scope to assign when one cannot be inferred.
    semantic_refs:
        Optional semantic context references (unused in v1, reserved
        for YAML semantic model matching).

    Returns
    -------
    list[DecisionCandidate]
        Candidates ready for human review or auto-commit.
    """
    candidates: list[DecisionCandidate] = []

    for fact in facts:
        decision_type, risk = _CATEGORY_MAP.get(
            fact.category, ("interpretation", RiskLevel.medium)
        )

        candidate_id = f"cand_{uuid4().hex[:10]}"

        # Build pre-filled decision contract
        candidate_decision = {
            "title": fact.statement,
            "scope": scope_default,
            "decision_type": decision_type,
            "rationale": f"Mined from conversation: {fact.evidence[0].quote if fact.evidence else fact.statement}",
            "activate": True,
        }

        candidates.append(
            DecisionCandidate(
                id=candidate_id,
                title=fact.statement,
                decision_type=decision_type,
                scope_suggestion=scope_default,
                risk=risk,
                confidence=fact.confidence,
                evidence=list(fact.evidence),
                rationale=candidate_decision["rationale"],
                candidate_decision=candidate_decision,
            )
        )

    return candidates
