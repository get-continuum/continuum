"""Continuum Demo API — dual-mode backend.

Set ``CONTINUUM_MODE=hosted`` to use Postgres (Neon) storage.
Defaults to ``local`` (file-based SDK storage).
"""

from __future__ import annotations

import hashlib
import os
import secrets
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from continuum.exceptions import ContinuumError

from auth.middleware import WorkspaceContext, require_workspace
from storage.base import StorageBackend
from storage.local import FileStorageBackend

# ---------------------------------------------------------------------------
# Backend factory
# ---------------------------------------------------------------------------

_backend_instance: Optional[StorageBackend] = None


def _default_store_dir() -> str:
    env = os.environ.get("CONTINUUM_STORE")
    if env:
        return env
    repo_root = Path(__file__).resolve().parents[2]
    return str(repo_root / ".continuum")


def _get_backend() -> StorageBackend:
    """Return the configured storage backend (singleton)."""
    global _backend_instance  # noqa: PLW0603
    if _backend_instance is not None:
        return _backend_instance

    mode = os.environ.get("CONTINUUM_MODE", "local")
    if mode == "hosted":
        from storage.postgres import PostgresStorageBackend

        database_url = os.environ.get("DATABASE_URL", "")
        if not database_url:
            raise RuntimeError("DATABASE_URL must be set when CONTINUUM_MODE=hosted")
        _backend_instance = PostgresStorageBackend(database_url=database_url)
    else:
        _backend_instance = FileStorageBackend(storage_dir=_default_store_dir())
    return _backend_instance


def get_backend() -> StorageBackend:
    """FastAPI dependency that provides the storage backend."""
    return _get_backend()


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="Continuum API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class ResolveRequest(BaseModel):
    prompt: str
    scope: str
    candidates: Optional[list[dict[str, Any]]] = None


class EnforceRequest(BaseModel):
    scope: str
    action: dict[str, Any] = Field(default_factory=dict)


class CommitRequest(BaseModel):
    title: str
    scope: str
    decision_type: str
    rationale: str
    options: Optional[list[dict[str, Any]]] = None
    stakeholders: Optional[list[str]] = None
    metadata: Optional[dict[str, Any]] = None
    override_policy: Optional[str] = None
    precedence: Optional[int] = None
    supersedes: Optional[str] = None
    activate: bool = False


class CommitSimpleRequest(BaseModel):
    """Simplified commit for quick decision capture from chat feedback."""

    title: str
    scope: str
    decision_type: str = "interpretation"
    rationale: Optional[str] = None


class SupersedeRequest(BaseModel):
    old_id: str
    new_title: str
    rationale: Optional[str] = None
    options: Optional[list[dict[str, Any]]] = None
    stakeholders: Optional[list[str]] = None
    metadata: Optional[dict[str, Any]] = None
    override_policy: Optional[str] = None
    precedence: Optional[int] = None


# -- Auth request models ---------------------------------------------------


class SignupRequest(BaseModel):
    email: str
    password: str
    workspace_name: str


class LoginRequest(BaseModel):
    email: str
    password: str


class CreateApiKeyRequest(BaseModel):
    name: str = "default"


# ---------------------------------------------------------------------------
# Core decision routes (unchanged response shapes)
# ---------------------------------------------------------------------------


@app.get("/health")
def health() -> dict[str, Any]:
    mode = os.environ.get("CONTINUUM_MODE", "local")
    return {"ok": True, "mode": mode}


@app.post("/commit_simple")
def commit_simple(
    req: CommitSimpleRequest,
    ws: WorkspaceContext = Depends(require_workspace),
    backend: StorageBackend = Depends(get_backend),
) -> dict[str, Any]:
    try:
        dec = backend.commit(
            title=req.title,
            scope=req.scope,
            decision_type=req.decision_type,
            rationale=req.rationale,
        )
        dec = backend.update_status(dec["id"], "active")
        return {"decision": dec, "workspace_id": ws.workspace_id}
    except ContinuumError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/inspect")
def inspect(
    scope: str,
    backend: StorageBackend = Depends(get_backend),
) -> dict[str, Any]:
    try:
        return {"binding": backend.inspect(scope)}
    except ContinuumError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/decision/{decision_id}")
def get_decision(
    decision_id: str,
    backend: StorageBackend = Depends(get_backend),
) -> dict[str, Any]:
    try:
        dec = backend.get(decision_id)
        return {"decision": dec}
    except ContinuumError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/resolve")
def resolve(
    req: ResolveRequest,
    backend: StorageBackend = Depends(get_backend),
) -> dict[str, Any]:
    try:
        res = backend.resolve(query=req.prompt, scope=req.scope, candidates=req.candidates)
        return {"resolution": res}
    except ContinuumError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/enforce")
def enforce(
    req: EnforceRequest,
    backend: StorageBackend = Depends(get_backend),
) -> dict[str, Any]:
    try:
        res = backend.enforce(action=req.action, scope=req.scope)
        return {"enforcement": res}
    except ContinuumError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/commit")
def commit(
    req: CommitRequest,
    backend: StorageBackend = Depends(get_backend),
) -> dict[str, Any]:
    try:
        dec = backend.commit(
            title=req.title,
            scope=req.scope,
            decision_type=req.decision_type,
            rationale=req.rationale,
            options=req.options,
            stakeholders=req.stakeholders,
            metadata=req.metadata,
            override_policy=req.override_policy,
            precedence=req.precedence,
            supersedes=req.supersedes,
        )
        if req.activate:
            dec = backend.update_status(dec["id"], "active")
        return {"decision": dec}
    except ContinuumError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/supersede")
def supersede(
    req: SupersedeRequest,
    backend: StorageBackend = Depends(get_backend),
) -> dict[str, Any]:
    try:
        dec = backend.supersede(
            old_id=req.old_id,
            new_title=req.new_title,
            rationale=req.rationale,
            options=req.options,
            stakeholders=req.stakeholders,
            metadata=req.metadata,
            override_policy=req.override_policy,
            precedence=req.precedence,
        )
        return {"decision": dec}
    except ContinuumError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ---------------------------------------------------------------------------
# Auth routes (hosted mode only — no-ops when auth disabled)
# ---------------------------------------------------------------------------


@app.post("/auth/signup")
def signup(req: SignupRequest) -> dict[str, Any]:
    """Create a new user + workspace.  Returns a JWT."""
    if os.environ.get("CONTINUUM_AUTH_ENABLED", "false").lower() != "true":
        raise HTTPException(status_code=404, detail="Auth not enabled")

    try:
        import bcrypt
        import jwt as pyjwt

        database_url = os.environ["DATABASE_URL"]
        jwt_secret = os.environ["JWT_SECRET"]
    except (ImportError, KeyError) as exc:
        raise HTTPException(status_code=500, detail=f"Auth misconfigured: {exc}")

    import psycopg
    from psycopg.rows import dict_row

    with psycopg.connect(database_url, row_factory=dict_row) as conn:
        # Check for existing user
        existing = conn.execute(
            "SELECT id FROM users WHERE email = %(email)s", {"email": req.email}
        ).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")

        # Create workspace
        ws_id = f"ws_{uuid4().hex[:12]}"
        conn.execute(
            "INSERT INTO workspaces (id, name) VALUES (%(id)s, %(name)s)",
            {"id": ws_id, "name": req.workspace_name},
        )

        # Create user
        user_id = f"usr_{uuid4().hex[:12]}"
        pw_hash = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode()
        conn.execute(
            """INSERT INTO users (id, email, password_hash, workspace_id)
               VALUES (%(id)s, %(email)s, %(pw)s, %(ws)s)""",
            {"id": user_id, "email": req.email, "pw": pw_hash, "ws": ws_id},
        )

    token = pyjwt.encode(
        {"user_id": user_id, "workspace_id": ws_id, "email": req.email},
        jwt_secret,
        algorithm="HS256",
    )
    return {
        "token": token,
        "user": {"id": user_id, "email": req.email},
        "workspace": {"id": ws_id, "name": req.workspace_name},
    }


@app.post("/auth/login")
def login(req: LoginRequest) -> dict[str, Any]:
    """Authenticate and return a JWT."""
    if os.environ.get("CONTINUUM_AUTH_ENABLED", "false").lower() != "true":
        raise HTTPException(status_code=404, detail="Auth not enabled")

    try:
        import bcrypt
        import jwt as pyjwt

        database_url = os.environ["DATABASE_URL"]
        jwt_secret = os.environ["JWT_SECRET"]
    except (ImportError, KeyError) as exc:
        raise HTTPException(status_code=500, detail=f"Auth misconfigured: {exc}")

    import psycopg
    from psycopg.rows import dict_row

    with psycopg.connect(database_url, row_factory=dict_row) as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE email = %(email)s", {"email": req.email}
        ).fetchone()

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not bcrypt.checkpw(req.password.encode(), user["password_hash"].encode()):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Fetch workspace name
    with psycopg.connect(database_url, row_factory=dict_row) as conn:
        ws = conn.execute(
            "SELECT * FROM workspaces WHERE id = %(id)s",
            {"id": user["workspace_id"]},
        ).fetchone()

    token = pyjwt.encode(
        {
            "user_id": user["id"],
            "workspace_id": user["workspace_id"],
            "email": user["email"],
        },
        jwt_secret,
        algorithm="HS256",
    )
    return {
        "token": token,
        "user": {"id": user["id"], "email": user["email"]},
        "workspace": {
            "id": user["workspace_id"],
            "name": ws["name"] if ws else "unknown",
        },
    }


@app.get("/auth/me")
def auth_me(
    ws: WorkspaceContext = Depends(require_workspace),
) -> dict[str, Any]:
    """Return the current user/workspace context."""
    return {
        "workspace_id": ws.workspace_id,
        "workspace_name": ws.workspace_name,
        "key_id": ws.key_id,
        "user_id": getattr(ws, "user_id", None),
        "email": getattr(ws, "email", None),
    }


# ---------------------------------------------------------------------------
# API key management routes
# ---------------------------------------------------------------------------


@app.get("/api-keys")
def list_api_keys(
    ws: WorkspaceContext = Depends(require_workspace),
) -> dict[str, Any]:
    """List API keys for the current workspace."""
    if os.environ.get("CONTINUUM_AUTH_ENABLED", "false").lower() != "true":
        return {"keys": []}

    import psycopg
    from psycopg.rows import dict_row

    database_url = os.environ["DATABASE_URL"]
    with psycopg.connect(database_url, row_factory=dict_row) as conn:
        rows = conn.execute(
            """SELECT id, name, created_at, substring(key_hash from 1 for 8) as hash_prefix
               FROM api_keys WHERE workspace_id = %(ws)s ORDER BY created_at""",
            {"ws": ws.workspace_id},
        ).fetchall()

    return {"keys": rows}


@app.post("/api-keys")
def create_api_key(
    req: CreateApiKeyRequest,
    ws: WorkspaceContext = Depends(require_workspace),
) -> dict[str, Any]:
    """Create a new API key.  Returns the raw key once."""
    if os.environ.get("CONTINUUM_AUTH_ENABLED", "false").lower() != "true":
        raise HTTPException(status_code=404, detail="Auth not enabled")

    import psycopg

    database_url = os.environ["DATABASE_URL"]
    key_id = f"key_{uuid4().hex[:12]}"
    raw_key = f"ctk_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    with psycopg.connect(database_url) as conn:
        conn.execute(
            """INSERT INTO api_keys (id, workspace_id, key_hash, name)
               VALUES (%(id)s, %(ws)s, %(hash)s, %(name)s)""",
            {"id": key_id, "ws": ws.workspace_id, "hash": key_hash, "name": req.name},
        )

    return {"key_id": key_id, "raw_key": raw_key, "name": req.name}


@app.delete("/api-keys/{key_id}")
def revoke_api_key(
    key_id: str,
    ws: WorkspaceContext = Depends(require_workspace),
) -> dict[str, Any]:
    """Revoke an API key."""
    if os.environ.get("CONTINUUM_AUTH_ENABLED", "false").lower() != "true":
        raise HTTPException(status_code=404, detail="Auth not enabled")

    import psycopg

    database_url = os.environ["DATABASE_URL"]
    with psycopg.connect(database_url) as conn:
        result = conn.execute(
            """DELETE FROM api_keys
               WHERE id = %(id)s AND workspace_id = %(ws)s""",
            {"id": key_id, "ws": ws.workspace_id},
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="API key not found")

    return {"deleted": True, "key_id": key_id}
