"""Pydantic v2 models for the Continuum decision framework."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict


class DecisionStatus(str, Enum):
    """Lifecycle status of a decision."""

    draft = "draft"
    active = "active"
    superseded = "superseded"
    archived = "archived"


class DecisionType(str, Enum):
    """Classification of the decision."""

    interpretation = "interpretation"
    rejection = "rejection"
    preference = "preference"
    behavior_rule = "behavior_rule"


class OverridePolicy(str, Enum):
    """How overrides are handled."""

    invalid_by_default = "invalid_by_default"
    warn = "warn"
    allow = "allow"


class Option(BaseModel):
    """An option considered during a decision."""

    model_config = ConfigDict(use_enum_values=True)

    id: str
    title: str
    selected: bool
    rejected_reason: Optional[str] = None


class DecisionContext(BaseModel):
    """Contextual information about when/why a decision was made."""

    model_config = ConfigDict(use_enum_values=True)

    trigger: str
    source: str
    timestamp: datetime
    actor: Optional[str] = None


class Enforcement(BaseModel):
    """Enforcement rules for a decision."""

    model_config = ConfigDict(use_enum_values=True)

    scope: str
    decision_type: DecisionType
    supersedes: Optional[str] = None
    precedence: Optional[int] = None
    override_policy: OverridePolicy = OverridePolicy.invalid_by_default


class Decision(BaseModel):
    """Core decision record."""

    model_config = ConfigDict(use_enum_values=True)

    id: str
    version: int = 0
    status: DecisionStatus = DecisionStatus.draft
    title: str
    rationale: Optional[str] = None
    options_considered: list[Option] = []
    context: Optional[DecisionContext] = None
    enforcement: Optional[Enforcement] = None
    stakeholders: list[str] = []
    metadata: dict = {}
    created_at: datetime
    updated_at: datetime
