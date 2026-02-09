"""Interfaces for integrating external memory systems.

Continuum is a decision layer. External memory systems (Mem0, Zep, Letta, etc.)
can act as *signal sources* that inform decision creation and updates.

This module defines minimal protocols so connectors can be implemented without
adding hard dependencies.
"""

from __future__ import annotations

from typing import Any, Protocol


class MemorySignalSource(Protocol):
    """A minimal interface for retrieving memory signals."""

    def search(self, query: str, *, scope: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
        """Return relevant memory records for *query*."""

