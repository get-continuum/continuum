"""Authority ranking for decision issuers.

Optional weights: admin > lead > member.  When a decision carries an
``issuer_type`` and/or ``authority`` field, this module produces a numeric
rank used for conflict tie-breaking.
"""

from __future__ import annotations

from typing import Any

_ISSUER_RANKS: dict[str, int] = {
    "system": 30,
    "human": 20,
    "agent": 10,
}

_AUTHORITY_RANKS: dict[str, int] = {
    "admin": 30,
    "lead": 20,
    "member": 10,
}


def authority_rank(decision: dict[str, Any]) -> int:
    """Return a numeric authority score for a decision.

    Uses ``issuer_type`` and ``authority`` fields from the decision or its
    metadata.  Returns 0 if neither field is present.
    """
    meta = decision.get("metadata") or {}
    enforcement = decision.get("enforcement") or {}
    if isinstance(enforcement, dict):
        issuer_type = enforcement.get("issuer_type") or meta.get("issuer_type", "")
        authority = enforcement.get("authority") or meta.get("authority", "")
    else:
        issuer_type = meta.get("issuer_type", "")
        authority = meta.get("authority", "")

    issuer_score = _ISSUER_RANKS.get(str(issuer_type), 0)
    authority_score = _AUTHORITY_RANKS.get(str(authority), 0)
    return issuer_score + authority_score
