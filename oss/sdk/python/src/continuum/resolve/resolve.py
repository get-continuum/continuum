"""Deterministic resolve function for the Continuum ambiguity gate."""

from __future__ import annotations

from continuum.resolve.types import CandidateOption, ClarificationRequest, ResolveResult


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
    query_lower = query.lower()

    for decision in decisions:
        decision_scope = _get_scope(decision)
        if decision_scope != scope:
            continue

        # Match on title keywords
        title = decision.get("title", "").lower()
        if not title:
            continue

        # Exact substring match: query words appear in title or vice-versa
        if title in query_lower or query_lower in title:
            return ResolveResult(
                status="resolved",
                resolved_context=decision,
                matched_decision_id=decision.get("id"),
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
