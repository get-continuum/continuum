"""De-duplicate near-identical decision candidates.

Uses simple title similarity (normalised token overlap) and scope overlap
to cluster candidates.  The highest-confidence candidate in each cluster
is kept; evidence from all cluster members is merged.
"""

from __future__ import annotations

from continuum_miner.types import DecisionCandidate


def _normalise_tokens(text: str) -> set[str]:
    """Lowercase, strip punctuation, return token set."""
    return {t.strip(".,!?;:\"'()[]") for t in text.lower().split() if t.strip(".,!?;:\"'()[]")}


def _title_similarity(a: str, b: str) -> float:
    """Token-overlap Jaccard similarity."""
    tokens_a = _normalise_tokens(a)
    tokens_b = _normalise_tokens(b)
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


def dedupe_candidates(
    candidates: list[DecisionCandidate],
    similarity_threshold: float = 0.7,
) -> list[DecisionCandidate]:
    """Remove near-duplicate candidates.

    Parameters
    ----------
    candidates:
        Raw candidates from :func:`extract_decision_candidates`.
    similarity_threshold:
        Jaccard similarity threshold above which two candidates are
        considered duplicates.  Default ``0.7``.

    Returns
    -------
    list[DecisionCandidate]
        De-duplicated candidates with merged evidence.
    """
    if not candidates:
        return []

    # Greedy clustering
    clusters: list[list[DecisionCandidate]] = []

    for cand in candidates:
        placed = False
        for cluster in clusters:
            representative = cluster[0]
            sim = _title_similarity(cand.title, representative.title)
            same_scope = cand.scope_suggestion == representative.scope_suggestion
            if sim >= similarity_threshold and same_scope:
                cluster.append(cand)
                placed = True
                break
        if not placed:
            clusters.append([cand])

    # Select best candidate per cluster, merge evidence
    result: list[DecisionCandidate] = []
    for cluster in clusters:
        best = max(cluster, key=lambda c: c.confidence)
        # Merge evidence from all members
        all_evidence = []
        seen_quotes: set[str] = set()
        for member in cluster:
            for ev in member.evidence:
                if ev.quote not in seen_quotes:
                    seen_quotes.add(ev.quote)
                    all_evidence.append(ev)
        best_copy = best.model_copy(update={"evidence": all_evidence})
        result.append(best_copy)

    return result
