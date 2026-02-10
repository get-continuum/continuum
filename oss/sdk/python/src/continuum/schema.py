"""JSON Schema loader and validator for Continuum decisions."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from continuum.exceptions import ValidationError

# oss/sdk/python/src/continuum/schema.py  ->  up 4 parents  ->  oss/
# Then into contracts/schemas/
SCHEMA_DIR: Path = Path(__file__).resolve().parents[4] / "contracts" / "schemas"


def load_schema(name: str) -> dict:
    """Load a JSON schema file by name.

    Parameters
    ----------
    name:
        Filename (with or without .json extension) inside the schemas directory.

    Returns
    -------
    dict
        Parsed JSON schema.
    """
    path = SCHEMA_DIR / name
    if not path.suffix:
        path = path.with_suffix(".json")
    with open(path) as fh:
        result: dict = json.load(fh)
        return result


def validate_decision(data: dict) -> None:
    """Validate *data* against ``decision.v0.schema.json``.

    Raises
    ------
    ValidationError
        If the data does not conform to the schema.
    """
    try:
        schema = load_schema("decision.v0.schema.json")
        jsonschema.validate(instance=data, schema=schema)
    except (jsonschema.ValidationError, jsonschema.SchemaError) as exc:
        raise ValidationError(str(exc)) from exc
    except FileNotFoundError as exc:
        raise ValidationError(f"Schema file not found: {exc}") from exc
