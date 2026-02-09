"""Deterministic resolve function for the Continuum ambiguity gate."""

from __future__ import annotations

from continuum.resolve.types import CandidateOption, ClarificationRequest, ResolveResult
from continuum.scope import scope_matches, scope_specificity


def resolve(
    query: str,
    scope: str,
    candidates: list[CandidateOption],
    decisions: list[dict],
) -> ResolveResult:
    """Resolve *query* against existing *decisions*.

    All logic is deterministic — exact string matching on scope and
    title keywords.  No scoring or LLM calls.

    Parameters
    ----------
    query:
        The free-text query describing the intent.
    scope:
        The scope to match decisions against.
    candidates:
        Caller-supplied candidate options for disambiguation.
    decisions:
        List of decision dicts (or Decision-like objects serialised to dict).

    Returns
    -------
    ResolveResult
        Either ``status="resolved"`` with the matched decision data,
        or ``status="needs_clarification"`` with a clarification request.
    """
    query_lower = query.lower().strip()

    matches: list[dict] = []
    for decision in decisions:
        if decision.get("status") != "active":
            continue

        decision_scope = _get_scope(decision)
        if not scope_matches(decision_scope, scope):
            continue

        title = decision.get("title", "").lower().strip()
        if not title:
            continue

        if title in query_lower or query_lower in title:
            matches.append(decision)

    if matches:
        def _rank(d: dict) -> tuple[int, int, str]:
            enforcement = d.get("enforcement") or {}
            if not isinstance(enforcement, dict):
                enforcement = {}
            precedence = int(enforcement.get("precedence") or 0)
            created_at = str(d.get("created_at") or "")
            return (
                scope_specificity(_get_scope(d)),
                precedence,
                created_at,
            )

        best = max(matches, key=_rank)
        return ResolveResult(
            status="resolved",
            resolved_context=best,
            matched_decision_id=best.get("id"),
        )

    # No matching decision found
    if candidates:
        return ResolveResult(
            status="needs_clarification",
            clarification=ClarificationRequest(
                question=f"Multiple options exist for '{query}'. Please select one.",
                candidates=candidates,
                context={"scope": scope, "query": query},
            ),
        )

    return ResolveResult(
        status="needs_clarification",
        clarification=ClarificationRequest(
            question="No prior decision found. Please clarify intent.",
            candidates=[],
            context={"scope": scope, "query": query},
        ),
    )


def _get_scope(decision: dict) -> str:
    """Extract scope from a decision dict."""
    enforcement = decision.get("enforcement")
    if isinstance(enforcement, dict):
        return enforcement.get("scope", "")
    return decision.get("scope", "")
