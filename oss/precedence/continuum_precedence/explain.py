"""Human-readable explanations for arbitration results."""

from __future__ import annotations

from typing import Any

from continuum_precedence.arbitrate import ArbitrationResult
from continuum_precedence.specificity import enhanced_specificity
from continuum_precedence.authority import authority_rank


def _get_scope(d: dict[str, Any]) -> str:
    enforcement = d.get("enforcement")
    if isinstance(enforcement, dict):
        return str(enforcement.get("scope", ""))
    return ""


def _get_precedence(d: dict[str, Any]) -> int:
    enforcement = d.get("enforcement")
    if isinstance(enforcement, dict):
        return int(enforcement.get("precedence") or 0)
    return 0


def explain_winner(result: ArbitrationResult) -> str:
    """Generate a human-readable explanation of why the winner was chosen.

    Parameters
    ----------
    result:
        The :class:`ArbitrationResult` from :func:`arbitrate`.

    Returns
    -------
    str
        A multi-sentence explanation suitable for UI display.
    """
    if not result.conflict_detected:
        if result.winner:
            return (
                f"Decision \"{result.winner.get('title', 'unknown')}\" "
                f"({result.winner.get('id', '?')}) is the only active decision "
                f"for this scope. No conflict."
            )
        return "No decisions found for this scope."

    winner = result.winner
    parts: list[str] = []
    w_title = winner.get("title", "unknown")
    w_id = winner.get("id", "?")
    w_scope = _get_scope(winner)
    w_prec = _get_precedence(winner)

    parts.append(
        f"Decision \"{w_title}\" ({w_id}) wins among "
        f"{len(result.losers) + 1} competing decisions."
    )

    # Explain why
    reasons: list[str] = []

    for loser in result.losers:
        l_scope = _get_scope(loser)
        l_prec = _get_precedence(loser)
        l_title = loser.get("title", "unknown")

        w_spec = enhanced_specificity(w_scope)
        l_spec = enhanced_specificity(l_scope)

        if w_prec > l_prec:
            reasons.append(
                f"It has higher explicit precedence ({w_prec}) than "
                f"\"{l_title}\" ({l_prec})."
            )
        elif w_spec > l_spec:
            reasons.append(
                f"Its scope \"{w_scope}\" is more specific than "
                f"\"{l_scope}\" (score {w_spec:.0f} vs {l_spec:.0f})."
            )
        elif authority_rank(winner) > authority_rank(loser):
            reasons.append(
                f"It has higher authority rank than \"{l_title}\"."
            )
        else:
            reasons.append(
                f"It was created more recently than \"{l_title}\"."
            )

    # De-duplicate reasons
    seen: set[str] = set()
    unique_reasons: list[str] = []
    for r in reasons:
        if r not in seen:
            seen.add(r)
            unique_reasons.append(r)

    parts.extend(unique_reasons)
    return " ".join(parts)
