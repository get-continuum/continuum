"""API key authentication middleware.

MVP auth: Bearer token in Authorization header, validated against
the api_keys table. Each key is scoped to a workspace.
"""

from __future__ import annotations

import hashlib
import os
from typing import Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel


class WorkspaceContext(BaseModel):
    """Resolved workspace from a validated API key."""

    workspace_id: str
    workspace_name: str
    key_id: str


# In-memory store for MVP; replace with DB lookup for production.
_API_KEYS: dict[str, WorkspaceContext] = {}

_bearer_scheme = HTTPBearer(auto_error=False)


def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def register_api_key(raw_key: str, workspace_id: str, workspace_name: str, key_id: str) -> None:
    """Register an API key (call at startup or via admin endpoint)."""
    _API_KEYS[_hash_key(raw_key)] = WorkspaceContext(
        workspace_id=workspace_id,
        workspace_name=workspace_name,
        key_id=key_id,
    )


def _resolve_key(raw_key: str) -> Optional[WorkspaceContext]:
    return _API_KEYS.get(_hash_key(raw_key))


async def require_workspace(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> WorkspaceContext:
    """FastAPI dependency that extracts and validates the workspace from the API key.

    When CONTINUUM_AUTH_DISABLED=1, returns a default workspace (useful for
    local dev and the demo).
    """
    if os.environ.get("CONTINUUM_AUTH_DISABLED", "1") == "1":
        return WorkspaceContext(
            workspace_id="ws_default",
            workspace_name="default",
            key_id="key_dev",
        )

    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    ctx = _resolve_key(credentials.credentials)
    if ctx is None:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return ctx
