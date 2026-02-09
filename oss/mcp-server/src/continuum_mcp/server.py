"""Continuum MCP Server.

Exposes Continuum decision operations as MCP tools:
  - inspect: Look up a decision by ID
  - resolve: Check if a prior decision covers a prompt
  - enforce: Evaluate enforcement rules for a decision
  - commit: Persist a new decision
"""

from __future__ import annotations

import json
import sys
from typing import Any

# ---------------------------------------------------------------------------
# MCP SDK imports — gracefully degrade if not installed
# ---------------------------------------------------------------------------
try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent

    _HAS_MCP = True
except ImportError:
    _HAS_MCP = False

# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

TOOLS: list[dict[str, Any]] = [
    {
        "name": "continuum_inspect",
        "description": "Inspect a decision by ID. Returns the full decision record.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "decision_id": {
                    "type": "string",
                    "description": "The unique decision identifier.",
                },
            },
            "required": ["decision_id"],
        },
    },
    {
        "name": "continuum_resolve",
        "description": (
            "Check whether a prior decision already covers the given prompt and scope. "
            "Returns resolved context or a needs_clarification signal."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The agent prompt to resolve against prior decisions.",
                },
                "scope": {
                    "type": "string",
                    "description": "Hierarchical scope identifier (e.g. repo:acme/backend).",
                },
            },
            "required": ["prompt", "scope"],
        },
    },
    {
        "name": "continuum_enforce",
        "description": (
            "Evaluate enforcement rules for a decision and action context. "
            "Returns a verdict: allow, confirm, or block."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "decision_id": {
                    "type": "string",
                    "description": "The decision to enforce.",
                },
                "action_context": {
                    "type": "object",
                    "description": "Context about the action being performed.",
                },
            },
            "required": ["decision_id"],
        },
    },
    {
        "name": "continuum_commit",
        "description": "Persist a new decision with title, scope, options, and rationale.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Short title describing the decision.",
                },
                "scope": {
                    "type": "string",
                    "description": "Hierarchical scope identifier.",
                },
                "decision_type": {
                    "type": "string",
                    "description": "Type of decision (e.g. rejection, selection).",
                },
                "options": {
                    "type": "array",
                    "description": "List of options considered.",
                    "items": {"type": "object"},
                },
                "rationale": {
                    "type": "string",
                    "description": "Why this decision was made.",
                },
            },
            "required": ["title", "scope", "decision_type", "rationale"],
        },
    },
]

# ---------------------------------------------------------------------------
# Tool handlers (stubs)
# ---------------------------------------------------------------------------


def _handle_inspect(arguments: dict[str, Any]) -> str:
    """Inspect a decision by ID."""
    # TODO: Wire up to ContinuumClient.inspect()
    decision_id = arguments.get("decision_id", "unknown")
    return json.dumps(
        {"status": "not_implemented", "decision_id": decision_id},
    )


def _handle_resolve(arguments: dict[str, Any]) -> str:
    """Resolve a prompt against prior decisions."""
    # TODO: Wire up to ContinuumClient.resolve()
    return json.dumps(
        {
            "status": "not_implemented",
            "prompt": arguments.get("prompt", ""),
            "scope": arguments.get("scope", ""),
        },
    )


def _handle_enforce(arguments: dict[str, Any]) -> str:
    """Enforce rules for a decision."""
    # TODO: Wire up to enforcement engine
    return json.dumps(
        {
            "status": "not_implemented",
            "decision_id": arguments.get("decision_id", "unknown"),
        },
    )


def _handle_commit(arguments: dict[str, Any]) -> str:
    """Commit a new decision."""
    # TODO: Wire up to ContinuumClient.commit()
    return json.dumps(
        {
            "status": "not_implemented",
            "title": arguments.get("title", ""),
        },
    )


_HANDLERS: dict[str, Any] = {
    "continuum_inspect": _handle_inspect,
    "continuum_resolve": _handle_resolve,
    "continuum_enforce": _handle_enforce,
    "continuum_commit": _handle_commit,
}

# ---------------------------------------------------------------------------
# Server setup
# ---------------------------------------------------------------------------


def main() -> None:
    """Start the Continuum MCP server."""
    if not _HAS_MCP:
        print(
            "ERROR: The 'mcp' package is not installed. "
            "Install it with: pip install 'mcp>=1.0'",
            file=sys.stderr,
        )
        sys.exit(1)

    server = Server("continuum-mcp")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [Tool(**t) for t in TOOLS]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        handler = _HANDLERS.get(name)
        if handler is None:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
        result = handler(arguments)
        return [TextContent(type="text", text=result)]

    import asyncio
    from mcp.server.stdio import stdio_server

    async def _run() -> None:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream)

    asyncio.run(_run())


if __name__ == "__main__":
    main()
