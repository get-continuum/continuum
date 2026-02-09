"""OSS Resolve / Ambiguity Gate module for Continuum.

Deterministic resolution of queries against recorded decisions.
"""

from __future__ import annotations

from continuum.resolve.resolve import resolve
from continuum.resolve.types import CandidateOption, ClarificationRequest, ResolveResult

__all__ = [
    "CandidateOption",
    "ClarificationRequest",
    "ResolveResult",
    "resolve",
]
