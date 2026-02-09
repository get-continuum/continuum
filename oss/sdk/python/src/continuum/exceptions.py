"""Continuum SDK exceptions."""

from __future__ import annotations


class ContinuumError(Exception):
    """Base exception for Continuum SDK."""


class ValidationError(ContinuumError):
    """Schema validation failed."""


class DecisionNotFoundError(ContinuumError):
    """Decision ID not found in storage."""


class TransitionError(ContinuumError):
    """Invalid lifecycle transition."""
