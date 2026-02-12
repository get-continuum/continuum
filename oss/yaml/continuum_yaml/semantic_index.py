"""Parse YAML semantic models into a queryable semantic index.

A SemanticIndex holds metrics, entities, and joins from one or more YAML
models, allowing phrase-based lookup to identify which model a query refers to.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


@dataclass
class MetricDef:
    """A metric definition from a semantic model."""

    name: str
    definition: str
    sql: str = ""
    table: str = ""
    model_name: str = ""
    dimensions: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class EntityDef:
    """An entity definition from a semantic model."""

    name: str
    table: str = ""
    primary_key: str = ""
    model_name: str = ""
    attributes: list[str] = field(default_factory=list)


@dataclass
class JoinDef:
    """A join definition from a semantic model."""

    name: str
    from_entity: str = ""
    to_entity: str = ""
    on_clause: str = ""
    join_type: str = "inner"
    model_name: str = ""


@dataclass
class SemanticIndex:
    """Queryable index of metrics, entities, and joins across models."""

    metrics: dict[str, list[MetricDef]] = field(default_factory=dict)
    entities: dict[str, list[EntityDef]] = field(default_factory=dict)
    joins: dict[str, list[JoinDef]] = field(default_factory=dict)
    model_names: list[str] = field(default_factory=list)

    def lookup_metric(self, name: str) -> list[MetricDef]:
        """Find all metric definitions matching *name* (case-insensitive)."""
        return self.metrics.get(name.lower(), [])

    def lookup_entity(self, name: str) -> list[EntityDef]:
        """Find all entity definitions matching *name*."""
        return self.entities.get(name.lower(), [])

    def has_ambiguity(self, metric_name: str) -> bool:
        """Return True if *metric_name* is defined in multiple models."""
        return len(self.lookup_metric(metric_name)) > 1


def parse_yaml_model(path: str | Path) -> dict[str, Any]:
    """Parse a single YAML semantic model file.

    Returns the raw dict.  Raises ImportError if PyYAML is not installed.
    """
    if yaml is None:
        raise ImportError("PyYAML is required: pip install pyyaml")
    with open(path) as f:
        return yaml.safe_load(f) or {}


def build_index(paths: list[str | Path]) -> SemanticIndex:
    """Build a :class:`SemanticIndex` from a list of YAML file paths."""
    index = SemanticIndex()

    for p in paths:
        raw = parse_yaml_model(p)
        model = raw.get("model", {})
        model_name = model.get("name", str(p))
        index.model_names.append(model_name)

        # Metrics
        for mname, mdef in raw.get("metrics", {}).items():
            key = mname.lower()
            metric = MetricDef(
                name=mname,
                definition=mdef.get("definition", ""),
                sql=mdef.get("sql", ""),
                table=mdef.get("table", ""),
                model_name=model_name,
                dimensions=mdef.get("dimensions", []),
                notes=mdef.get("notes", ""),
            )
            index.metrics.setdefault(key, []).append(metric)

        # Entities
        for ename, edef in raw.get("entities", {}).items():
            key = ename.lower()
            entity = EntityDef(
                name=ename,
                table=edef.get("table", ""),
                primary_key=edef.get("primary_key", ""),
                model_name=model_name,
                attributes=edef.get("attributes", []),
            )
            index.entities.setdefault(key, []).append(entity)

        # Joins
        for jname, jdef in raw.get("joins", {}).items():
            key = jname.lower()
            join = JoinDef(
                name=jname,
                from_entity=jdef.get("from", ""),
                to_entity=jdef.get("to", ""),
                on_clause=jdef.get("on", ""),
                join_type=jdef.get("type", "inner"),
                model_name=model_name,
            )
            index.joins.setdefault(key, []).append(join)

    return index
