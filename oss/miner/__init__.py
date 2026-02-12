"""Continuum Mining Module — extract facts and decision candidates from conversations.

The miner uses deterministic, rules-first extraction.  Every candidate carries
traceable evidence and a risk level so that downstream consumers (UI, CLI, MCP)
can present them for human review or auto-commit via policy.

The main implementation lives in the ``continuum_miner`` sub-package.
This top-level ``__init__.py`` provides convenient re-exports.
"""

