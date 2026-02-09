from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from continuum.client import ContinuumClient
from continuum.exceptions import ContinuumError


def _default_store_dir() -> str:
    env = os.environ.get("CONTINUUM_STORE")
    if env:
        return env
    repo_root = Path(__file__).resolve().parents[2]
    return str(repo_root / ".continuum")


def _client() -> ContinuumClient:
    return ContinuumClient(storage_dir=_default_store_dir())


app = FastAPI(title="Continuum Demo API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


class SupersedeRequest(BaseModel):
    old_id: str
    new_title: str
    rationale: Optional[str] = None
    options: Optional[list[dict[str, Any]]] = None
    stakeholders: Optional[list[str]] = None
    metadata: Optional[dict[str, Any]] = None
    override_policy: Optional[str] = None
    precedence: Optional[int] = None


@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "store_dir": _default_store_dir()}


@app.get("/inspect")
def inspect(scope: str) -> dict[str, Any]:
    try:
        return {"binding": _client().inspect(scope)}
    except ContinuumError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/decision/{decision_id}")
def get_decision(decision_id: str) -> dict[str, Any]:
    try:
        dec = _client().get(decision_id)
        return {"decision": dec.model_dump(mode="json")}
    except ContinuumError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/resolve")
def resolve(req: ResolveRequest) -> dict[str, Any]:
    try:
        res = _client().resolve(query=req.prompt, scope=req.scope, candidates=req.candidates)
        return {"resolution": res}
    except ContinuumError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/enforce")
def enforce(req: EnforceRequest) -> dict[str, Any]:
    try:
        res = _client().enforce(action=req.action, scope=req.scope)
        return {"enforcement": res}
    except ContinuumError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/commit")
def commit(req: CommitRequest) -> dict[str, Any]:
    try:
        client = _client()
        dec = client.commit(
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
            dec = client.update_status(dec.id, "active")
        return {"decision": dec.model_dump(mode="json")}
    except ContinuumError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/supersede")
def supersede(req: SupersedeRequest) -> dict[str, Any]:
    try:
        client = _client()
        dec = client.supersede(
            old_id=req.old_id,
            new_title=req.new_title,
            rationale=req.rationale,
            options=req.options,
            stakeholders=req.stakeholders,
            metadata=req.metadata,
            override_policy=req.override_policy,
            precedence=req.precedence,
        )
        return {"decision": dec.model_dump(mode="json")}
    except ContinuumError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

