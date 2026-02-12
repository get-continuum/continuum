"""Rules-first fact extractor.

Scans conversation text for patterns that indicate preferences, constraints,
rejections, interpretations, and behavior rules.  Every extracted fact carries
an :class:`EvidenceSpan` so callers can trace it back to the source.

The extractor is intentionally deterministic — no ML or LLM calls.
"""

from __future__ import annotations

import re
from uuid import uuid4

from continuum_miner.types import EvidenceSpan, Fact

# ---------------------------------------------------------------------------
# Pattern definitions — (category, compiled regex, confidence)
# ---------------------------------------------------------------------------

_PATTERNS: list[tuple[str, re.Pattern[str], float]] = [
    # Preferences
    (
        "preference",
        re.compile(
            r"(?:i\s+)?(?:prefer|like|want|love|always\s+(?:use|choose|go\s+with))\s+(.+?)(?:\.|$)",
            re.IGNORECASE,
        ),
        0.85,
    ),
    # Constraints / budgets / limits
    (
        "constraint",
        re.compile(
            r"(?:budget|limit|max(?:imum)?|cap|no\s+more\s+than|at\s+most|under)\s*(?:is|of|:)?\s*(.+?)(?:\.|$)",
            re.IGNORECASE,
        ),
        0.90,
    ),
    # Must / should / need to
    (
        "constraint",
        re.compile(
            r"(?:must|should|need\s+to|have\s+to|require)\s+(.+?)(?:\.|$)",
            re.IGNORECASE,
        ),
        0.80,
    ),
    # Rejections
    (
        "rejection",
        re.compile(
            r"(?:don'?t|do\s+not|never|avoid|no)\s+(?:want|use|like|include|allow)\s+(.+?)(?:\.|$)",
            re.IGNORECASE,
        ),
        0.90,
    ),
    # Interpretations — "X means Y" / "by X we mean Y"
    (
        "interpretation",
        re.compile(
            r"(?:by\s+.+?\s+(?:we\s+)?mean|.+?\s+(?:means?|refers?\s+to|is\s+defined\s+as))\s+(.+?)(?:\.|$)",
            re.IGNORECASE,
        ),
        0.85,
    ),
    # Behavior rules — "always …" / "whenever …"
    (
        "behavior_rule",
        re.compile(
            r"(?:always|whenever|every\s+time|each\s+time|make\s+sure\s+to)\s+(.+?)(?:\.|$)",
            re.IGNORECASE,
        ),
        0.80,
    ),
    # Dietary / travel constraints (domain patterns)
    (
        "constraint",
        re.compile(
            r"(?:i'?m|i\s+am)\s+(?:vegetarian|vegan|gluten[- ]free|lactose[- ]intolerant|allergic\s+to\s+\w+)",
            re.IGNORECASE,
        ),
        0.95,
    ),
    (
        "constraint",
        re.compile(
            r"(?:no\s+(?:flights?|flying)|(?:afraid|scared)\s+of\s+flying|can'?t\s+fly)",
            re.IGNORECASE,
        ),
        0.95,
    ),
]


def extract_facts(text: str) -> list[Fact]:
    """Extract facts from a conversation or block of text.

    Parameters
    ----------
    text:
        Free-text conversation content.

    Returns
    -------
    list[Fact]
        Extracted facts with evidence spans.
    """
    facts: list[Fact] = []
    seen_statements: set[str] = set()

    for category, pattern, confidence in _PATTERNS:
        for match in pattern.finditer(text):
            statement = match.group(0).strip().rstrip(".")
            # Normalise to avoid near-identical duplicates from the same text
            norm = statement.lower().strip()
            if norm in seen_statements:
                continue
            seen_statements.add(norm)

            evidence = EvidenceSpan(
                source_type="conversation",
                source_ref="",
                span_start=match.start(),
                span_end=match.end(),
                quote=match.group(0).strip(),
            )

            facts.append(
                Fact(
                    id=f"fact_{uuid4().hex[:10]}",
                    category=category,
                    statement=statement,
                    evidence=[evidence],
                    confidence=confidence,
                )
            )

    return facts
