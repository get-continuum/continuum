#!/usr/bin/env python3
"""Manual MCP smoke test.

This script starts the Continuum MCP server over stdio, calls a few tools,
and verifies the repo-local store is consistent with the local SDK.

Prereqs:
  pip install continuum-mcp-server continuum-sdk "mcp>=1.0"
"""

from __future__ import annotations

import asyncio
import os
import tempfile


async def _run() -> int:
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
    except Exception as exc:  # pragma: no cover
        print("ERROR: Missing MCP client deps. Install with: pip install 'mcp>=1.0'")
        print(f"Details: {exc}")
        return 1

    from continuum.client import ContinuumClient

    with tempfile.TemporaryDirectory() as td:
        store_dir = os.path.join(td, ".continuum")

        server_params = StdioServerParameters(
            command="python3",
            args=["-m", "continuum_mcp.server", "serve"],
            env={**os.environ, "CONTINUUM_STORE": store_dir},
        )

        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()

                scope = "repo:smoke"

                commit_res = await session.call_tool(
                    "continuum_commit",
                    {
                        "title": "Reject full rewrites",
                        "scope": scope,
                        "decision_type": "rejection",
                        "options": [
                            {"title": "Incremental refactor", "selected": True},
                            {
                                "title": "Full rewrite",
                                "selected": False,
                                "rejected_reason": "Too risky",
                            },
                        ],
                        "rationale": "Prefer incremental refactors.",
                        "activate": True,
                    },
                )
                print("commit:", commit_res)

                inspect_res = await session.call_tool(
                    "continuum_inspect",
                    {"scope": scope},
                )
                print("inspect(scope):", inspect_res)

                resolve_res = await session.call_tool(
                    "continuum_resolve",
                    {
                        "prompt": "Reject full rewrites",
                        "scope": scope,
                    },
                )
                print("resolve:", resolve_res)

                # Verify local SDK sees the same store.
                client = ContinuumClient(storage_dir=store_dir)
                binding = client.inspect(scope)
                assert any(d["title"] == "Reject full rewrites" for d in binding)

        print("SMOKE TEST PASSED")
        return 0


def main() -> None:
    raise SystemExit(asyncio.run(_run()))


if __name__ == "__main__":
    main()

