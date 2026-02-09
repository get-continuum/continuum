"""Types for the resolve / ambiguity-gate module."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class CandidateOption(BaseModel):
    """A candidate option supplied by the caller."""

    id: str
    title: str
    source: str = "caller"
    confidence: float = 0.5


class ClarificationRequest(BaseModel):
    """A request for the caller to clarify intent."""

    question: str
    candidates: list[CandidateOption]
    context: dict = {}


class ResolveResult(BaseModel):
    """Result of the resolve operation."""

    status: str  # "resolved" | "needs_clarification"
    resolved_context: Optional[dict] = None
    clarification: Optional[ClarificationRequest] = None
    matched_decision_id: Optional[str] = None
