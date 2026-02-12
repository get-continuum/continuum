"""Continuum MCP Server.

Exposes Continuum decision operations as MCP tools:
  - inspect: binding set by scope OR a decision by ID
  - resolve: ambiguity gate against prior decisions
  - enforce: enforcement verdict for a proposed action
  - commit: persist a new decision (optionally activate)
  - supersede: replace an existing decision with a new active one
"""

from __future__ import annotations

import os
import json
import sys
from typing import Any

# SDK
from continuum.client import ContinuumClient
from continuum.exceptions import ContinuumError

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
        "name": "continuum_mine",
        "description": (
            "Extract facts and decision candidates from conversation text. "
            "Returns structured facts and candidates ready for review or commit."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "conversations": {
                    "type": "array",
                    "description": "List of conversation strings to mine.",
                    "items": {"type": "string"},
                },
                "scope_default": {
                    "type": "string",
                    "description": "Default scope for mined candidates (e.g. repo:acme/backend).",
                },
                "semantic_context_refs": {
                    "type": "array",
                    "description": "Optional semantic context references.",
                    "items": {"type": "string"},
                },
            },
            "required": ["conversations", "scope_default"],
        },
    },
    {
        "name": "continuum_commit_from_clarification",
        "description": (
            "Commit a decision from a clarification response. "
            "Takes the chosen option and scope to create an active decision."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "chosen_option_id": {
                    "type": "string",
                    "description": "ID of the selected clarification option.",
                },
                "scope": {
                    "type": "string",
                    "description": "Scope to commit the decision in.",
                },
                "title": {
                    "type": "string",
                    "description": "Title for the decision (optional, defaults to option title).",
                },
                "decision_type": {
                    "type": "string",
                    "description": "Decision type (default: interpretation).",
                    "default": "interpretation",
                },
                "rationale": {
                    "type": "string",
                    "description": "Rationale for the decision.",
                },
            },
            "required": ["chosen_option_id", "scope"],
        },
    },
    {
        "name": "continuum_inspect",
        "description": (
            "Inspect Continuum decisions. Provide either `decision_id` to fetch a single decision, "
            "or `scope` to fetch the active binding set for that scope."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "decision_id": {
                    "type": "string",
                    "description": "The unique decision identifier.",
                },
                "scope": {
                    "type": "string",
                    "description": "Scope to inspect (returns active binding set).",
                },
            },
            "anyOf": [{"required": ["decision_id"]}, {"required": ["scope"]}],
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
                "candidates": {
                    "type": "array",
                    "description": "Optional candidate options (id, title) for disambiguation.",
                    "items": {"type": "object"},
                },
            },
            "required": ["prompt", "scope"],
        },
    },
    {
        "name": "continuum_enforce",
        "description": (
            "Evaluate enforcement rules for a proposed action in a scope. "
            "Returns a verdict: allow, confirm, or block (deterministic)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "scope": {
                    "type": "string",
                    "description": "Scope to evaluate enforcement within.",
                },
                "action": {
                    "type": "object",
                    "description": "Proposed action (type, description, metadata).",
                },
            },
            "required": ["scope", "action"],
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
                "stakeholders": {
                    "type": "array",
                    "description": "Optional list of stakeholders.",
                    "items": {"type": "string"},
                },
                "metadata": {
                    "type": "object",
                    "description": "Optional decision metadata.",
                },
                "override_policy": {
                    "type": "string",
                    "description": "Override policy: invalid_by_default | warn | allow",
                },
                "precedence": {
                    "type": "integer",
                    "description": "Optional precedence for conflict resolution.",
                },
                "supersedes": {
                    "type": "string",
                    "description": "Optional decision id this decision supersedes.",
                },
                "activate": {
                    "type": "boolean",
                    "description": "If true, transition the decision to active immediately.",
                    "default": False,
                },
            },
            "required": ["title", "scope", "decision_type", "rationale"],
        },
    },
    {
        "name": "continuum_supersede",
        "description": "Supersede an existing decision by committing a replacement and activating it.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "old_id": {
                    "type": "string",
                    "description": "ID of the decision being replaced.",
                },
                "new_title": {
                    "type": "string",
                    "description": "Title for the replacement decision.",
                },
                "rationale": {
                    "type": "string",
                    "description": "Rationale for the replacement decision.",
                },
                "options": {
                    "type": "array",
                    "description": "Optional list of options considered.",
                    "items": {"type": "object"},
                },
                "stakeholders": {
                    "type": "array",
                    "description": "Optional list of stakeholders.",
                    "items": {"type": "string"},
                },
                "metadata": {
                    "type": "object",
                    "description": "Optional decision metadata.",
                },
                "override_policy": {
                    "type": "string",
                    "description": "Override policy: invalid_by_default | warn | allow",
                },
                "precedence": {
                    "type": "integer",
                    "description": "Optional precedence for conflict resolution.",
                },
            },
            "required": ["old_id", "new_title"],
        },
    },
]

# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------


def _client() -> ContinuumClient:
    storage_dir = os.environ.get("CONTINUUM_STORE")
    return ContinuumClient(storage_dir=storage_dir) if storage_dir else ContinuumClient()


def _ok(payload: Any) -> str:
    return json.dumps({"status": "ok", "result": payload}, default=str)


def _err(message: str) -> str:
    return json.dumps({"status": "error", "error": message})


def _handle_inspect(arguments: dict[str, Any]) -> str:
    """Inspect by decision_id (single record) OR by scope (binding set)."""
    try:
        client = _client()
        if "decision_id" in arguments and arguments["decision_id"]:
            dec = client.get(str(arguments["decision_id"]))
            return _ok(dec.model_dump(mode="json"))
        if "scope" in arguments and arguments["scope"]:
            binding = client.inspect(str(arguments["scope"]))
            return _ok(binding)
        return _err("Provide either 'decision_id' or 'scope'.")
    except ContinuumError as exc:
        return _err(str(exc))


def _handle_resolve(arguments: dict[str, Any]) -> str:
    """Resolve a prompt against prior decisions."""
    try:
        client = _client()
        prompt = str(arguments.get("prompt", ""))
        scope = str(arguments.get("scope", ""))
        candidates = arguments.get("candidates")
        result = client.resolve(query=prompt, scope=scope, candidates=candidates)
        return _ok(result)
    except ContinuumError as exc:
        return _err(str(exc))


def _handle_enforce(arguments: dict[str, Any]) -> str:
    """Enforce rules for a proposed action within a scope."""
    try:
        client = _client()
        scope = str(arguments.get("scope", ""))
        action = arguments.get("action") or {}
        result = client.enforce(action=action, scope=scope)
        return _ok(result)
    except ContinuumError as exc:
        return _err(str(exc))


def _handle_commit(arguments: dict[str, Any]) -> str:
    """Commit a new decision."""
    try:
        client = _client()
        dec = client.commit(
            title=str(arguments["title"]),
            scope=str(arguments["scope"]),
            decision_type=str(arguments["decision_type"]),
            options=arguments.get("options"),
            rationale=arguments.get("rationale"),
            stakeholders=arguments.get("stakeholders"),
            metadata=arguments.get("metadata"),
            override_policy=arguments.get("override_policy"),
            precedence=arguments.get("precedence"),
            supersedes=arguments.get("supersedes"),
        )
        if arguments.get("activate"):
            dec = client.update_status(dec.id, "active")
        return _ok(dec.model_dump(mode="json"))
    except (KeyError, TypeError) as exc:
        return _err(f"Invalid arguments: {exc}")
    except ContinuumError as exc:
        return _err(str(exc))


def _handle_supersede(arguments: dict[str, Any]) -> str:
    """Supersede an existing decision."""
    try:
        client = _client()
        dec = client.supersede(
            old_id=str(arguments["old_id"]),
            new_title=str(arguments["new_title"]),
            rationale=arguments.get("rationale"),
            options=arguments.get("options"),
            stakeholders=arguments.get("stakeholders"),
            metadata=arguments.get("metadata"),
            override_policy=arguments.get("override_policy"),
            precedence=arguments.get("precedence"),
        )
        return _ok(dec.model_dump(mode="json"))
    except (KeyError, TypeError) as exc:
        return _err(f"Invalid arguments: {exc}")
    except ContinuumError as exc:
        return _err(str(exc))


def _handle_mine(arguments: dict[str, Any]) -> str:
    """Mine conversations for facts and decision candidates."""
    try:
        import sys
        from pathlib import Path

        # Add oss/miner to path
        miner_root = Path(__file__).resolve().parents[4] / "miner"
        if str(miner_root) not in sys.path:
            sys.path.insert(0, str(miner_root))

        from continuum_miner.extract_facts import extract_facts
        from continuum_miner.extract_decision_candidates import extract_decision_candidates
        from continuum_miner.dedupe_merge import dedupe_candidates

        conversations = arguments.get("conversations", [])
        scope_default = str(arguments.get("scope_default", ""))
        semantic_refs = arguments.get("semantic_context_refs")

        all_facts = []
        for convo in conversations:
            all_facts.extend(extract_facts(str(convo)))

        candidates = extract_decision_candidates(
            facts=all_facts,
            scope_default=scope_default,
            semantic_refs=semantic_refs,
        )
        deduped = dedupe_candidates(candidates)

        return _ok({
            "facts": [f.model_dump(mode="json") for f in all_facts],
            "decision_candidates": [c.model_dump(mode="json") for c in deduped],
        })
    except Exception as exc:
        return _err(str(exc))


def _handle_commit_from_clarification(arguments: dict[str, Any]) -> str:
    """Commit a decision from a clarification response."""
    try:
        client = _client()
        title = arguments.get("title") or f"Clarification: {arguments.get('chosen_option_id', '')}"
        scope = str(arguments.get("scope", ""))
        decision_type = str(arguments.get("decision_type", "interpretation"))
        rationale = arguments.get("rationale") or f"Selected option: {arguments.get('chosen_option_id', '')}"

        dec = client.commit(
            title=title,
            scope=scope,
            decision_type=decision_type,
            rationale=rationale,
            metadata={"clarification_option_id": arguments.get("chosen_option_id", "")},
        )
        dec = client.update_status(dec.id, "active")
        return _ok(dec.model_dump(mode="json"))
    except (KeyError, TypeError) as exc:
        return _err(f"Invalid arguments: {exc}")
    except ContinuumError as exc:
        return _err(str(exc))


_HANDLERS: dict[str, Any] = {
    "continuum_mine": _handle_mine,
    "continuum_commit_from_clarification": _handle_commit_from_clarification,
    "continuum_inspect": _handle_inspect,
    "continuum_resolve": _handle_resolve,
    "continuum_enforce": _handle_enforce,
    "continuum_commit": _handle_commit,
    "continuum_supersede": _handle_supersede,
}

# ---------------------------------------------------------------------------
# Server setup
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry point for the `continuum-mcp` console script.

    Usage:
        continuum-mcp serve

    Environment:
        CONTINUUM_STORE=/path/to/.continuum
    """
    # Minimal CLI wrapper (avoid extra deps).
    cmd = sys.argv[1] if len(sys.argv) > 1 else "serve"
    if cmd in ("-h", "--help", "help"):
        print(
            "Continuum MCP Server\n\n"
            "Usage:\n"
            "  continuum-mcp serve\n\n"
            "Environment:\n"
            "  CONTINUUM_STORE   Path to repo-local .continuum directory\n",
            file=sys.stdout,
        )
        return
    if cmd != "serve":
        print(f"Unknown command: {cmd}\nRun: continuum-mcp --help", file=sys.stderr)
        sys.exit(2)

    serve()


def serve() -> None:
    """Start the Continuum MCP server (stdio transport)."""
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
            init_options = server.create_initialization_options()
            await server.run(read_stream, write_stream, init_options)

    asyncio.run(_run())


if __name__ == "__main__":
    main()
