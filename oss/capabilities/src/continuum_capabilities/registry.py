"""Capability registry — defines available modules and their dependencies."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Capability:
    """A named capability that can be toggled on/off."""

    name: str
    description: str
    depends_on: list[str] = field(default_factory=list)
    enabled: bool = False
    _factory: Callable[..., object] | None = field(default=None, repr=False)

    def enable(self) -> None:
        self.enabled = True

    def disable(self) -> None:
        self.enabled = False


class CapabilityRegistry:
    """Registry of all available Continuum capabilities.

    Capabilities are modules that can be toggled per environment.
    The registry validates dependency ordering so you can't enable
    a module without its dependencies.

    Example
    -------
    >>> registry = CapabilityRegistry()
    >>> registry.register(Capability(name="store", description="Local decision store"))
    >>> registry.register(Capability(name="engine", description="Resolve/enforce engine", depends_on=["store"]))
    >>> registry.enable("store")
    >>> registry.enable("engine")
    """

    def __init__(self) -> None:
        self._capabilities: dict[str, Capability] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, capability: Capability) -> None:
        """Register a capability. Raises ValueError on duplicate names."""
        if capability.name in self._capabilities:
            raise ValueError(f"Capability '{capability.name}' already registered")
        self._capabilities[capability.name] = capability

    # ------------------------------------------------------------------
    # Enable / disable
    # ------------------------------------------------------------------

    def enable(self, name: str) -> None:
        """Enable a capability, validating that all dependencies are enabled first."""
        cap = self._get(name)
        for dep in cap.depends_on:
            dep_cap = self._get(dep)
            if not dep_cap.enabled:
                raise RuntimeError(
                    f"Cannot enable '{name}': dependency '{dep}' is not enabled"
                )
        cap.enable()

    def disable(self, name: str) -> None:
        """Disable a capability, validating no other enabled capability depends on it."""
        cap = self._get(name)
        dependents = [
            c.name
            for c in self._capabilities.values()
            if c.enabled and name in c.depends_on
        ]
        if dependents:
            raise RuntimeError(
                f"Cannot disable '{name}': required by {dependents}"
            )
        cap.disable()

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def is_enabled(self, name: str) -> bool:
        """Check if a capability is enabled."""
        return self._get(name).enabled

    def list_enabled(self) -> list[str]:
        """Return names of all enabled capabilities."""
        return [c.name for c in self._capabilities.values() if c.enabled]

    def list_all(self) -> list[Capability]:
        """Return all registered capabilities."""
        return list(self._capabilities.values())

    def get(self, name: str) -> Capability:
        """Get a capability by name."""
        return self._get(name)

    # ------------------------------------------------------------------
    # Built-in capabilities (convenience factory)
    # ------------------------------------------------------------------

    @classmethod
    def default(cls) -> "CapabilityRegistry":
        """Create a registry pre-loaded with standard Continuum capabilities."""
        registry = cls()
        registry.register(Capability(
            name="store",
            description="Local file-backed decision store",
        ))
        registry.register(Capability(
            name="engine",
            description="Resolve and enforce engine",
            depends_on=["store"],
        ))
        registry.register(Capability(
            name="mcp",
            description="MCP server exposing Continuum tools",
            depends_on=["store", "engine"],
        ))
        registry.register(Capability(
            name="cli",
            description="CLI inspector",
            depends_on=["store", "engine"],
        ))
        registry.register(Capability(
            name="api",
            description="REST API server",
            depends_on=["store", "engine"],
        ))
        registry.register(Capability(
            name="auth",
            description="Authentication and workspace tenancy",
            depends_on=["api"],
        ))
        registry.register(Capability(
            name="ambiguity_gate",
            description="Ambiguity Gate UI component",
            depends_on=["engine"],
        ))
        registry.register(Capability(
            name="inspector",
            description="Decision Inspector UI component",
            depends_on=["store"],
        ))
        return registry

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _get(self, name: str) -> Capability:
        if name not in self._capabilities:
            raise KeyError(f"Unknown capability: '{name}'")
        return self._capabilities[name]
