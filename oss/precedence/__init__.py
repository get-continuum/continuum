"""Continuum Precedence Engine — deterministic conflict arbitration.

Provides scope ranking, authority weights, specificity scoring, and
human-readable explanations for conflict resolution.
"""

from continuum_precedence.arbitrate import arbitrate, ArbitrationResult
from continuum_precedence.explain import explain_winner
from continuum_precedence.scope_rank import scope_type_rank
from continuum_precedence.specificity import enhanced_specificity
from continuum_precedence.authority import authority_rank

__all__ = [
    "arbitrate",
    "ArbitrationResult",
    "explain_winner",
    "scope_type_rank",
    "enhanced_specificity",
    "authority_rank",
]
