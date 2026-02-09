"""Scope parsing and matching utilities.

Continuum scopes are prefix-based and may be *chained* to express hierarchy,
using ``/`` as a segment separator.

Examples:
  - ``repo:acme/backend``
  - ``repo:acme/backend/folder:src/api/auth``
  - ``repo:acme/backend/folder:src/api/auth/user:alice``

This module provides deterministic matching used by list/inspect/resolve/enforce.
"""

from __future__ import annotations

from fnmatch import fnmatchcase


def split_scope(scope: str) -> list[str]:
    """Split a scope string into non-empty segments."""
    return [seg for seg in scope.split("/") if seg]


def scope_matches(prefix_scope: str, target_scope: str) -> bool:
    """Return True if *prefix_scope* applies to *target_scope*.

    Matching is segment-boundary prefix matching:
      - ``repo:acme/backend`` matches ``repo:acme/backend`` and
        ``repo:acme/backend/folder:src``.

    Wildcards (``*``) are supported inside segments, e.g.:
      - ``repo:*`` matches any repo segment such as ``repo:acme/backend``.
    """
    if not prefix_scope or not target_scope:
        return False

    prefix_parts = split_scope(prefix_scope)
    target_parts = split_scope(target_scope)

    if len(prefix_parts) > len(target_parts):
        return False

    for i, prefix_seg in enumerate(prefix_parts):
        if not fnmatchcase(target_parts[i], prefix_seg):
            return False
    return True


def scope_specificity(scope: str) -> int:
    """Specificity score for conflict resolution (higher = more specific)."""
    return len(split_scope(scope))

