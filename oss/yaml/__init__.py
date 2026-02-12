"""Continuum YAML Semantic Module — parse YAML semantic models into queryable dictionaries."""

from continuum_yaml.semantic_index import SemanticIndex, parse_yaml_model
from continuum_yaml.matchers import match_phrase

__all__ = ["SemanticIndex", "parse_yaml_model", "match_phrase"]
