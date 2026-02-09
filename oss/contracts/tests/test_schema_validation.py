"""Schema validation tests for Continuum Contracts.

Tests validate example JSON documents against their JSON Schemas using the
``jsonschema`` library. These tests ensure that:
- Valid examples pass schema validation.
- Invalid examples fail schema validation as expected.
- Schemas contain required meta fields.
"""

import pytest
from jsonschema import Draft202012Validator, ValidationError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_validator(schema: dict) -> Draft202012Validator:
    """Create a Draft 2020-12 validator, skipping $ref resolution.

    We inline-resolve the context $ref by removing it and instead validating
    the context sub-object directly against the context schema where needed.
    """
    # Work on a copy so fixtures are not mutated
    schema_copy = dict(schema)
    # Remove $ref from context property so the main schema validates standalone
    props = schema_copy.get("properties", {})
    if "context" in props and "$ref" in props["context"]:
        # Replace $ref with a permissive object type for standalone validation
        props["context"] = {"type": "object"}
    return Draft202012Validator(schema_copy)


# ---------------------------------------------------------------------------
# Valid example tests
# ---------------------------------------------------------------------------

class TestValidExamples:
    """Tests that valid example documents pass schema validation."""

    def test_valid_code_decision_passes(
        self, decision_schema: dict, valid_code_decision: dict
    ):
        """valid-code-decision.json must validate against the decision schema."""
        validator = _make_validator(decision_schema)
        # Should not raise
        validator.validate(valid_code_decision)

    def test_valid_interpretation_decision_passes(
        self, decision_schema: dict, valid_interpretation_decision: dict
    ):
        """valid-interpretation-decision.json must validate against the decision schema."""
        validator = _make_validator(decision_schema)
        # Should not raise
        validator.validate(valid_interpretation_decision)


# ---------------------------------------------------------------------------
# Invalid example tests
# ---------------------------------------------------------------------------

class TestInvalidExamples:
    """Tests that invalid example documents fail schema validation."""

    def test_invalid_missing_required_fails(
        self, decision_schema: dict, invalid_missing_required: dict
    ):
        """invalid-missing-required.json must fail validation (missing id, version, status)."""
        validator = _make_validator(decision_schema)
        with pytest.raises(ValidationError):
            validator.validate(invalid_missing_required)

    def test_invalid_bad_enum_fails(
        self, decision_schema: dict, invalid_bad_transition: dict
    ):
        """invalid-bad-transition.json must fail validation (decision_type not in enum)."""
        validator = _make_validator(decision_schema)
        with pytest.raises(ValidationError):
            validator.validate(invalid_bad_transition)


# ---------------------------------------------------------------------------
# Schema meta-field tests
# ---------------------------------------------------------------------------

class TestSchemaMeta:
    """Tests that schemas contain required meta fields."""

    def test_schema_has_required_meta_fields(self, decision_schema: dict):
        """The decision schema must contain $id and schema_version."""
        assert "$id" in decision_schema, "Schema missing '$id' field"
        assert "schema_version" in decision_schema, "Schema missing 'schema_version' field"
        assert decision_schema["$id"] == "https://getcontinuum.dev/schemas/decision.v0.schema.json"
        assert decision_schema["schema_version"] == "0.1.0"

    def test_context_schema_has_meta_fields(self, context_schema: dict):
        """The context schema must contain $id and schema_version."""
        assert "$id" in context_schema
        assert "schema_version" in context_schema

    def test_status_schema_has_meta_fields(self, decision_status_schema: dict):
        """The status schema must contain $id and schema_version."""
        assert "$id" in decision_status_schema
        assert "schema_version" in decision_status_schema


# ---------------------------------------------------------------------------
# Context schema tests
# ---------------------------------------------------------------------------

class TestContextSchema:
    """Tests for the context sub-schema."""

    def test_context_schema_validates(
        self, context_schema: dict, valid_code_decision: dict
    ):
        """The context portion of a valid decision must validate against the context schema."""
        validator = Draft202012Validator(context_schema)
        context_data = valid_code_decision["context"]
        # Should not raise
        validator.validate(context_data)

    def test_context_schema_rejects_missing_trigger(self, context_schema: dict):
        """Context missing required 'trigger' field must fail validation."""
        validator = Draft202012Validator(context_schema)
        bad_context = {
            "source": "pull_request",
            "timestamp": "2025-01-14T16:00:00Z"
        }
        with pytest.raises(ValidationError):
            validator.validate(bad_context)

    def test_context_schema_allows_additional_properties(self, context_schema: dict):
        """Context schema allows additional properties for extensibility."""
        validator = Draft202012Validator(context_schema)
        extended_context = {
            "trigger": "code_review",
            "source": "github",
            "timestamp": "2025-01-14T16:00:00Z",
            "custom_field": "this should be allowed"
        }
        # Should not raise
        validator.validate(extended_context)
