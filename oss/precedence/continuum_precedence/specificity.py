"""Enhanced key specificity scoring.

Extends the basic segment-count specificity from ``oss/sdk/python`` with
weighted depth scoring that accounts for scope type.
"""

from __future__ import annotations

from continuum_precedence.scope_rank import scope_type_rank


def enhanced_specificity(scope: str) -> float:
    """Compute a specificity score that combines depth and type rank.

    Parameters
    ----------
    scope:
        A hierarchical scope string like ``repo:acme/backend/folder:src``.

    Returns
    -------
    float
        A composite specificity score (higher = more specific).
    """
    segments = [seg for seg in scope.split("/") if seg]
    depth = len(segments)
    type_rank = scope_type_rank(scope)
    # Composite: depth contributes 10 points per segment, plus type rank
    return depth * 10.0 + type_rank
