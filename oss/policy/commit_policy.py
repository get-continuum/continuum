"""Auto-commit policy for mined decision candidates.

Determines whether a candidate should be auto-committed or requires
human confirmation.  All logic is deterministic.
"""

from __future__ import annotations

from typing import Any


def should_auto_commit(candidate: dict[str, Any]) -> bool:
    """Return ``True`` if the candidate qualifies for auto-commit.

    Rules
    -----
    - ``risk`` must be ``"low"``
    - ``confidence`` must be >= 0.9
    - ``decision_type`` must be one of ``behavior_rule``, ``preference``
    """
    risk = candidate.get("risk", "medium")
    confidence = candidate.get("confidence", 0.0)
    decision_type = candidate.get("decision_type", "")

    return (
        risk == "low"
        and confidence >= 0.9
        and decision_type in ("behavior_rule", "preference")
    )
