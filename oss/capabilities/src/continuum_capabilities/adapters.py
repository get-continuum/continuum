"""Adapter interfaces for optional integrations.

These abstract base classes define extension points. Implementations
live in separate packages (or in continuum-core for BSL-licensed ones).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ModelAdapter(ABC):
    """Adapter for LLM model integrations.

    Implementations might use OpenAI, Anthropic, local models, etc.
    Used by core resolvers for ambiguity scoring and intent matching.
    """

    @abstractmethod
    async def complete(self, prompt: str, **kwargs: Any) -> str:
        """Generate a completion for the given prompt."""
        ...

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate an embedding vector for the given text."""
        ...


class OrchestratorAdapter(ABC):
    """Adapter for workflow orchestrator integrations.

    Implementations hook into LangGraph, CrewAI, or other agent frameworks.
    """

    @abstractmethod
    def inject_node(self, graph: Any, node_name: str, **kwargs: Any) -> Any:
        """Inject a Continuum decision node into an orchestrator graph."""
        ...

    @abstractmethod
    def get_state(self) -> dict[str, Any]:
        """Get the current orchestrator state relevant to decisions."""
        ...


class MemorySignalSource(ABC):
    """Adapter for memory/context signal sources.

    Implementations connect to mem0, Zep, SQLite, or other memory stores
    to enrich resolution candidates with prior context.

    Note: This is the same interface as ``continuum.memory.MemorySignalSource``
    in the SDK. This re-export exists so capability-level code can reference
    it without importing SDK internals.
    """

    @abstractmethod
    def search(
        self,
        query: str,
        *,
        scope: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Search for memory signals matching a query.

        Returns a list of dicts with at least ``id`` and ``content`` keys.
        """
        ...

    @abstractmethod
    def store(self, content: str, metadata: dict[str, Any] | None = None) -> str:
        """Store a new memory signal. Returns the signal ID."""
        ...
