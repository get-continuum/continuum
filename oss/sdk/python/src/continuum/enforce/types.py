"""Types for the enforcement module."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class ActionType(str, Enum):
    """Classification of an action being evaluated."""

    code_change = "code_change"
    migration = "migration"
    api_break = "api_break"
    deployment = "deployment"
    config_change = "config_change"
    generic = "generic"


class Action(BaseModel):
    """An action to be evaluated against enforcement rules."""

    type: ActionType
    description: str
    scope: str
    metadata: dict = {}


class EnforcementVerdict(str, Enum):
    """Outcome of enforcement evaluation."""

    allow = "allow"
    block = "block"
    confirm = "confirm"
    override = "override"


class EnforcementResult(BaseModel):
    """Result of evaluating an action against decisions."""

    verdict: EnforcementVerdict
    reason: str
    matched_decisions: list[str] = []
    required_confirmations: list[str] = []


class EnforcementRule(BaseModel):
    """A named enforcement rule."""

    name: str
    action_types: list[ActionType]
    verdict: EnforcementVerdict
    description: str
