"""Types for the Continuum mining module.

All types are Pydantic v2 models for consistency with the rest of the SDK.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict


class RiskLevel(str, Enum):
    """Risk classification for a mined decision candidate."""

    low = "low"
    medium = "medium"
    high = "high"


class EvidenceSpan(BaseModel):
    """A span of text that supports a fact or candidate."""

    model_config = ConfigDict(use_enum_values=True)

    source_type: str = "conversation"  # conversation | feedback | yaml
    source_ref: str = ""  # e.g. message index, filename
    span_start: int = 0
    span_end: int = 0
    quote: str = ""


class Fact(BaseModel):
    """An extracted fact from a conversation.

    Facts are normalised evidence — a preference, constraint, rejection,
    or interpretation expressed by a participant.
    """

    model_config = ConfigDict(use_enum_values=True)

    id: str
    category: str  # preference | constraint | rejection | interpretation | behavior_rule
    statement: str  # normalised phrasing
    evidence: list[EvidenceSpan] = []
    confidence: float = 0.8


class DecisionCandidate(BaseModel):
    """A candidate decision ready for human review or auto-commit.

    Each candidate is a pre-filled decision contract enriched with mining
    metadata (risk, confidence, evidence).
    """

    model_config = ConfigDict(use_enum_values=True)

    id: str
    title: str
    decision_type: str = "interpretation"
    scope_suggestion: str = ""
    risk: RiskLevel = RiskLevel.medium
    confidence: float = 0.5
    evidence: list[EvidenceSpan] = []
    rationale: str = ""
    candidate_decision: dict = {}  # pre-filled decision contract payload


class MineResult(BaseModel):
    """Result of the mining pipeline."""

    model_config = ConfigDict(use_enum_values=True)

    facts: list[Fact] = []
    decision_candidates: list[DecisionCandidate] = []
