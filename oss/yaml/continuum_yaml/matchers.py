"""Map natural language phrases to semantic concepts.

Provides deterministic matching of query phrases against metric names,
entity names, and dimension names in a :class:`SemanticIndex`.
"""

from __future__ import annotations

from dataclasses import dataclass

from continuum_yaml.semantic_index import SemanticIndex, MetricDef


@dataclass
class MatchResult:
    """Result of matching a phrase against the semantic index."""

    phrase: str
    matched_metrics: list[MetricDef]
    is_ambiguous: bool
    model_names: list[str]


def _normalise(text: str) -> list[str]:
    """Tokenise and normalise a phrase."""
    return [t.strip(".,!?;:\"'()[]").lower() for t in text.split() if t.strip(".,!?;:\"'()[]")]


def match_phrase(phrase: str, index: SemanticIndex) -> MatchResult:
    """Match a natural-language *phrase* against metrics in *index*.

    Looks for metric names embedded in the phrase using token overlap.
    Returns a :class:`MatchResult` indicating whether the match is ambiguous
    (i.e. the metric exists in multiple models).

    Parameters
    ----------
    phrase:
        Free-text query like "revenue by country last week".
    index:
        Semantic index built from YAML models.

    Returns
    -------
    MatchResult
        Contains matched metrics, ambiguity flag, and which models contribute.
    """
    tokens = _normalise(phrase)
    matched: list[MetricDef] = []

    for metric_key, definitions in index.metrics.items():
        metric_tokens = _normalise(metric_key.replace("_", " "))
        # Check if metric tokens appear in the phrase
        if all(mt in tokens for mt in metric_tokens):
            matched.extend(definitions)

    model_names = sorted({m.model_name for m in matched})
    return MatchResult(
        phrase=phrase,
        matched_metrics=matched,
        is_ambiguous=len(model_names) > 1,
        model_names=model_names,
    )
