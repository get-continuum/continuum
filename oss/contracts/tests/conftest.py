"""Shared pytest fixtures for Continuum Contracts schema validation tests."""

import json
from pathlib import Path

import pytest

# Resolve paths relative to this file
CONTRACTS_DIR = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = CONTRACTS_DIR / "schemas"
EXAMPLES_DIR = CONTRACTS_DIR / "examples"


def _load_json(path: Path) -> dict:
    """Load and parse a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Schema fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def decision_schema() -> dict:
    """Load the main Decision JSON Schema."""
    return _load_json(SCHEMAS_DIR / "decision.v0.schema.json")


@pytest.fixture(scope="session")
def decision_status_schema() -> dict:
    """Load the Decision Status JSON Schema."""
    return _load_json(SCHEMAS_DIR / "decision-status.v0.schema.json")


@pytest.fixture(scope="session")
def context_schema() -> dict:
    """Load the Context JSON Schema."""
    return _load_json(SCHEMAS_DIR / "context.v0.schema.json")


# ---------------------------------------------------------------------------
# Example fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def valid_code_decision() -> dict:
    """Load the valid code decision example."""
    return _load_json(EXAMPLES_DIR / "valid-code-decision.json")


@pytest.fixture(scope="session")
def valid_interpretation_decision() -> dict:
    """Load the valid interpretation decision example."""
    return _load_json(EXAMPLES_DIR / "valid-interpretation-decision.json")


@pytest.fixture(scope="session")
def invalid_missing_required() -> dict:
    """Load the invalid example with missing required fields."""
    return _load_json(EXAMPLES_DIR / "invalid-missing-required.json")


@pytest.fixture(scope="session")
def invalid_bad_transition() -> dict:
    """Load the invalid example with bad enum value."""
    return _load_json(EXAMPLES_DIR / "invalid-bad-transition.json")
