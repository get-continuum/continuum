"""Abstract base classes for extensible hooks.

These ABCs define the contract that plug-in implementations must satisfy.
No concrete implementations are provided in the core SDK.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from continuum.models import Decision


class AmbiguityScorer(ABC):
    """Score how ambiguous a decision is (0 = crystal-clear, 1 = totally ambiguous)."""

    @abstractmethod
    def score(self, decision: Decision) -> float:
        """Return an ambiguity score in [0, 1]."""


class DecisionCompiler(ABC):
    """Compile a decision into enforceable rules."""

    @abstractmethod
    def compile(self, decision: Decision) -> dict:
        """Return a dictionary of compiled rules."""


class RiskScorer(ABC):
    """Score the risk associated with a decision given additional context."""

    @abstractmethod
    def score(self, decision: Decision, context: dict) -> float:
        """Return a risk score in [0, 1]."""
