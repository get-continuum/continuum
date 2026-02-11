"""Dual authentication middleware: JWT (UI) + API key (programmatic).

When ``CONTINUUM_AUTH_ENABLED=true``:
  - Tokens starting with ``ctk_`` are treated as API keys and looked up
    in the ``api_keys`` table via SHA-256 hash.
  - All other Bearer tokens are decoded as JWTs signed with ``JWT_SECRET``.

When ``CONTINUUM_AUTH_ENABLED`` is unset or ``false`` (default / local mode):
  - Returns a default workspace context — no auth required.
"""

from __future__ import annotations

import hashlib
import os
from typing import Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel


class WorkspaceContext(BaseModel):
    """Resolved workspace from a validated credential."""

    workspace_id: str
    workspace_name: str
    key_id: str
    user_id: Optional[str] = None
    email: Optional[str] = None


_bearer_scheme = HTTPBearer(auto_error=False)


def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _resolve_api_key(raw_key: str) -> Optional[WorkspaceContext]:
    """Look up an API key (ctk_…) in the Postgres api_keys table."""
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError:
        return None

    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url:
        return None

    key_hash = _hash_key(raw_key)
    with psycopg.connect(database_url, row_factory=dict_row) as conn:
        row = conn.execute(
            """SELECT ak.id, ak.workspace_id, ak.name AS key_name, w.name AS ws_name
               FROM api_keys ak
               JOIN workspaces w ON w.id = ak.workspace_id
               WHERE ak.key_hash = %(hash)s""",
            {"hash": key_hash},
        ).fetchone()

    if row is None:
        return None

    return WorkspaceContext(
        workspace_id=row["workspace_id"],
        workspace_name=row["ws_name"],
        key_id=row["id"],
    )


def _resolve_jwt(token: str) -> Optional[WorkspaceContext]:
    """Decode a JWT and return the workspace context."""
    try:
        import jwt as pyjwt
    except ImportError:
        return None

    jwt_secret = os.environ.get("JWT_SECRET", "")
    if not jwt_secret:
        return None

    try:
        payload = pyjwt.decode(token, jwt_secret, algorithms=["HS256"])
    except pyjwt.PyJWTError:
        return None

    # Fetch workspace name from DB
    ws_name = payload.get("workspace_id", "unknown")
    try:
        import psycopg
        from psycopg.rows import dict_row

        database_url = os.environ.get("DATABASE_URL", "")
        if database_url:
            with psycopg.connect(database_url, row_factory=dict_row) as conn:
                ws_row = conn.execute(
                    "SELECT name FROM workspaces WHERE id = %(id)s",
                    {"id": payload.get("workspace_id")},
                ).fetchone()
                if ws_row:
                    ws_name = ws_row["name"]
    except Exception:
        pass

    return WorkspaceContext(
        workspace_id=payload.get("workspace_id", ""),
        workspace_name=ws_name,
        key_id="jwt",
        user_id=payload.get("user_id"),
        email=payload.get("email"),
    )


async def require_workspace(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> WorkspaceContext:
    """FastAPI dependency that extracts and validates the workspace.

    Supports both JWT tokens (UI sessions) and API keys (programmatic, ``ctk_``
    prefix).  When ``CONTINUUM_AUTH_ENABLED`` is not ``true``, returns a default
    workspace (local dev / demo mode).
    """
    if os.environ.get("CONTINUUM_AUTH_ENABLED", "false").lower() != "true":
        return WorkspaceContext(
            workspace_id="ws_default",
            workspace_name="default",
            key_id="key_dev",
        )

    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = credentials.credentials

    # API key flow (ctk_ prefix)
    if token.startswith("ctk_"):
        ctx = _resolve_api_key(token)
        if ctx is None:
            raise HTTPException(status_code=401, detail="Invalid API key")
        return ctx

    # JWT flow
    ctx = _resolve_jwt(token)
    if ctx is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return ctx
