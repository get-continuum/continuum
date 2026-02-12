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

_local_backend_instance: Optional[StorageBackend] = None


def _default_store_dir() -> str:
    env = os.environ.get("CONTINUUM_STORE")
    if env:
        return env
    repo_root = Path(__file__).resolve().parents[2]
    return str(repo_root / ".continuum")


def get_backend(
    ws: WorkspaceContext = Depends(require_workspace),
) -> StorageBackend:
    """FastAPI dependency — returns a workspace-scoped storage backend.

    In hosted mode a fresh ``PostgresStorageBackend`` is created per request so
    that it uses the authenticated user's ``workspace_id``.  In local mode the
    file-backed singleton is reused (workspace is ignored).
    """
    mode = os.environ.get("CONTINUUM_MODE", "local")
    if mode == "hosted":
        from storage.postgres import PostgresStorageBackend

        database_url = os.environ.get("DATABASE_URL", "")
        if not database_url:
            raise RuntimeError("DATABASE_URL must be set when CONTINUUM_MODE=hosted")
        return PostgresStorageBackend(
            database_url=database_url,
            workspace_id=ws.workspace_id,
        )

    global _local_backend_instance  # noqa: PLW0603
    if _local_backend_instance is None:
        _local_backend_instance = FileStorageBackend(storage_dir=_default_store_dir())
    return _local_backend_instance


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


class EvidenceInput(BaseModel):
    """Evidence span to link to a committed decision."""

    source_type: str = "conversation"
    source_ref: str = ""
    span_start: int = 0
    span_end: int = 0
    quote: str = ""


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
    evidence: Optional[list[EvidenceInput]] = None


class MineRequest(BaseModel):
    """Request body for the /mine endpoint."""

    conversations: list[str]
    scope_default: str
    semantic_context_refs: Optional[list[str]] = None


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


class CommitFromClarificationRequest(BaseModel):
    """Commit a decision from a clarification response."""

    chosen_option_id: str
    scope: str
    candidate_decision: Optional[dict[str, Any]] = None
    title: Optional[str] = None
    decision_type: str = "interpretation"
    rationale: Optional[str] = None


class UpdateStatusRequest(BaseModel):
    status: str


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


@app.post("/mine")
def mine_conversations(
    req: MineRequest,
    ws: WorkspaceContext = Depends(require_workspace),
    backend: StorageBackend = Depends(get_backend),
) -> dict[str, Any]:
    """Extract facts and decision candidates from conversations."""
    try:
        import sys
        from pathlib import Path

        # Add oss/miner to path so the mining module is importable
        miner_root = Path(__file__).resolve().parents[2] / "oss" / "miner"
        if str(miner_root) not in sys.path:
            sys.path.insert(0, str(miner_root))

        from continuum_miner.types import MineResult
        from continuum_miner.extract_facts import extract_facts
        from continuum_miner.extract_decision_candidates import extract_decision_candidates
        from continuum_miner.dedupe_merge import dedupe_candidates

        all_facts = []
        for convo in req.conversations:
            all_facts.extend(extract_facts(convo))

        candidates = extract_decision_candidates(
            facts=all_facts,
            scope_default=req.scope_default,
            semantic_refs=req.semantic_context_refs,
        )

        deduped = dedupe_candidates(candidates)

        # Apply auto-commit policy
        policy_root = Path(__file__).resolve().parents[2] / "oss" / "policy"
        if str(policy_root) not in sys.path:
            sys.path.insert(0, str(policy_root))

        from commit_policy import should_auto_commit

        auto_committed = []
        remaining = []
        for cand in deduped:
            cand_dict = cand.model_dump(mode="json")
            if should_auto_commit(cand_dict):
                # Auto-commit via backend
                payload = cand.candidate_decision
                dec = backend.commit(
                    title=str(payload.get("title", cand.title)),
                    scope=str(payload.get("scope", cand.scope_suggestion)),
                    decision_type=str(payload.get("decision_type", cand.decision_type)),
                    rationale=str(payload.get("rationale", cand.rationale)),
                )
                dec = backend.update_status(dec["id"], "active")
                auto_committed.append(dec)
            else:
                remaining.append(cand_dict)

        return {
            "facts": [f.model_dump(mode="json") for f in all_facts],
            "decision_candidates": remaining,
            "auto_committed": auto_committed,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


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
        binding = backend.inspect(scope)

        # Detect conflicts using precedence engine
        conflict_notes: list[dict[str, Any]] = []
        if len(binding) > 1:
            try:
                import sys as _sys
                from pathlib import Path as _Path

                prec_root = _Path(__file__).resolve().parents[2] / "oss" / "precedence"
                if str(prec_root) not in _sys.path:
                    _sys.path.insert(0, str(prec_root))

                from continuum_precedence.arbitrate import arbitrate
                from continuum_precedence.explain import explain_winner

                # Group decisions by title similarity to find conflicts
                result = arbitrate(binding, scope=scope)
                if result.conflict_detected:
                    conflict_notes.append({
                        "type": "precedence_conflict",
                        "winner_id": result.winner.get("id"),
                        "loser_ids": [l.get("id") for l in result.losers],
                        "explanation": explain_winner(result),
                        "scores": result.scores,
                    })
            except Exception:
                pass  # Graceful degradation if precedence module unavailable

        return {"binding": binding, "conflict_notes": conflict_notes}
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


@app.post("/commit_from_clarification")
def commit_from_clarification(
    req: CommitFromClarificationRequest,
    ws: WorkspaceContext = Depends(require_workspace),
    backend: StorageBackend = Depends(get_backend),
) -> dict[str, Any]:
    """Commit a decision from a clarification selection."""
    try:
        # Use candidate_decision if provided, otherwise build from request fields
        payload = req.candidate_decision or {}
        title = req.title or str(payload.get("title", f"Clarification: {req.chosen_option_id}"))
        scope = req.scope or str(payload.get("scope", ""))
        decision_type = str(payload.get("decision_type", req.decision_type))
        rationale = req.rationale or str(
            payload.get("rationale", f"Selected option: {req.chosen_option_id}")
        )

        dec = backend.commit(
            title=title,
            scope=scope,
            decision_type=decision_type,
            rationale=rationale,
            metadata={"clarification_option_id": req.chosen_option_id},
        )
        dec = backend.update_status(dec["id"], "active")

        # Return updated inspect
        binding = backend.inspect(scope)
        return {"decision": dec, "binding": binding}
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


@app.get("/decisions")
def list_decisions(
    scope: Optional[str] = None,
    backend: StorageBackend = Depends(get_backend),
) -> dict[str, Any]:
    """Return all decisions, optionally filtered by scope."""
    try:
        decs = backend.list_decisions(scope=scope if scope else None)
        return {"decisions": decs}
    except ContinuumError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/graph/decisions")
def graph_decisions(
    scope: Optional[str] = None,
    backend: StorageBackend = Depends(get_backend),
) -> dict[str, Any]:
    """Return decision graph data: nodes (decisions + scopes) and edges (supersedes, scope relationships)."""
    try:
        decs = backend.list_decisions(scope=scope if scope else None)

        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []
        scope_nodes: set[str] = set()

        for dec in decs:
            # Decision node
            nodes.append({
                "id": dec["id"],
                "type": "decision",
                "data": {
                    "title": dec.get("title", ""),
                    "status": dec.get("status", ""),
                    "decision_type": (dec.get("enforcement") or {}).get("decision_type", ""),
                    "created_at": dec.get("created_at", ""),
                },
            })

            # Scope node
            enforcement = dec.get("enforcement") or {}
            dec_scope = enforcement.get("scope", "")
            if dec_scope and dec_scope not in scope_nodes:
                scope_nodes.add(dec_scope)
                nodes.append({
                    "id": f"scope:{dec_scope}",
                    "type": "scope",
                    "data": {"scope": dec_scope},
                })

            # Edge: decision -> scope
            if dec_scope:
                edges.append({
                    "id": f"e-{dec['id']}-scope:{dec_scope}",
                    "source": dec["id"],
                    "target": f"scope:{dec_scope}",
                    "type": "applies_to",
                })

            # Edge: supersedes
            supersedes = enforcement.get("supersedes")
            if supersedes:
                edges.append({
                    "id": f"e-{dec['id']}-sup-{supersedes}",
                    "source": dec["id"],
                    "target": supersedes,
                    "type": "supersedes",
                })

        return {"nodes": nodes, "edges": edges}
    except ContinuumError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.patch("/decision/{decision_id}/status")
def update_decision_status(
    decision_id: str,
    req: UpdateStatusRequest,
    backend: StorageBackend = Depends(get_backend),
) -> dict[str, Any]:
    """Update the status of a decision (active, draft, archived)."""
    try:
        dec = backend.update_status(decision_id, req.status)
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
