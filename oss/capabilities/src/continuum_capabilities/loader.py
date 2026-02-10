"""Load and validate a continuum.yaml configuration file."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field

from continuum_capabilities.registry import CapabilityRegistry


class ContinuumConfig(BaseModel):
    """Parsed continuum.yaml configuration."""

    version: str = "0.1"
    mode: str = "local"  # "local" | "hosted" | "demo"
    capabilities: list[str] = Field(default_factory=list)
    store: StoreConfig = Field(default_factory=lambda: StoreConfig())
    adapters: AdapterConfig = Field(default_factory=lambda: AdapterConfig())


class StoreConfig(BaseModel):
    """Store configuration."""

    backend: str = "file"  # "file" | "sqlite" | "postgres"
    path: str = ".continuum"


class AdapterConfig(BaseModel):
    """Adapter configuration for optional integrations."""

    model: Optional[str] = None  # e.g. "openai", "anthropic"
    orchestrator: Optional[str] = None  # e.g. "langgraph", "crewai"
    memory: Optional[str] = None  # e.g. "mem0", "zep", "sqlite"


# Pre-defined capability sets for each mode
MODE_CAPABILITIES: dict[str, list[str]] = {
    "local": ["store", "engine", "mcp", "cli"],
    "hosted": ["store", "engine", "api", "auth"],
    "demo": ["store", "engine", "ambiguity_gate", "inspector"],
}


def load_config(path: str | Path | None = None) -> ContinuumConfig:
    """Load configuration from a YAML file.

    Searches in order:
    1. Explicit ``path`` argument
    2. ``./continuum.yaml``
    3. ``~/.continuum/config.yaml``

    If no file is found, returns a default (local-mode) config.
    """
    search_paths = [
        Path(path) if path else None,
        Path("continuum.yaml"),
        Path.home() / ".continuum" / "config.yaml",
    ]

    for p in search_paths:
        if p is not None and p.exists():
            raw = yaml.safe_load(p.read_text(encoding="utf-8"))
            if raw is None:
                raw = {}
            return ContinuumConfig(**raw)

    # No config found — return default
    return ContinuumConfig()


def apply_config(config: ContinuumConfig, registry: CapabilityRegistry | None = None) -> CapabilityRegistry:
    """Apply a configuration to a capability registry.

    Enables the capabilities specified in config, falling back to the
    mode's default capability set when none are explicitly listed.
    """
    if registry is None:
        registry = CapabilityRegistry.default()

    caps = config.capabilities or MODE_CAPABILITIES.get(config.mode, [])

    # Enable capabilities in dependency order
    for cap_name in caps:
        _enable_with_deps(registry, cap_name)

    return registry


def _enable_with_deps(registry: CapabilityRegistry, name: str) -> None:
    """Recursively enable a capability and its dependencies."""
    cap = registry.get(name)
    if cap.enabled:
        return
    for dep in cap.depends_on:
        _enable_with_deps(registry, dep)
    registry.enable(name)
