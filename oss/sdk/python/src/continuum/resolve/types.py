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
    impact_preview: Optional[str] = None


class ClarificationRequest(BaseModel):
    """A request for the caller to clarify intent."""

    question: str
    candidates: list[CandidateOption]
    context: dict = {}
    suggested_scope: Optional[str] = None
    candidate_decision: Optional[dict] = None


class ClarificationResponse(BaseModel):
    """A response to a clarification request."""

    chosen_option_id: str
    scope: str
    commit: bool = True


class ResolveResult(BaseModel):
    """Result of the resolve operation."""

    status: str  # "resolved" | "needs_clarification"
    resolved_context: Optional[dict] = None
    clarification: Optional[ClarificationRequest] = None
    matched_decision_id: Optional[str] = None
