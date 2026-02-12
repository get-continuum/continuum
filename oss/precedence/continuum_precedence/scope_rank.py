"""Scope hierarchy ranking.

Maps scope prefixes to a numeric rank.  Higher rank means more specific
in the organisational hierarchy.

Ranking:  user > channel > team > org > repo > global
"""

from __future__ import annotations

# Prefix → rank (higher = more authoritative at the individual level)
_SCOPE_TYPE_RANKS: dict[str, int] = {
    "user": 60,
    "channel": 50,
    "team": 40,
    "org": 30,
    "repo": 20,
    "folder": 25,
    "workflow": 15,
    "global": 10,
}

_DEFAULT_RANK = 10


def scope_type_rank(scope: str) -> int:
    """Return the hierarchy rank for the first prefix in *scope*.

    Examples
    --------
    >>> scope_type_rank("user:alice")
    60
    >>> scope_type_rank("team:eng")
    40
    >>> scope_type_rank("repo:acme/backend/folder:src")
    20
    """
    prefix = scope.split(":")[0] if ":" in scope else ""
    return _SCOPE_TYPE_RANKS.get(prefix, _DEFAULT_RANK)
