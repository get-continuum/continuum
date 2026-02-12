"""HTTP backend for the Continuum MCP server.

Proxies all decision operations to a hosted Continuum API via HTTP.
Uses only ``urllib.request`` (stdlib) to avoid extra dependencies.
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error
import urllib.parse
from typing import Any, Optional


class HttpBackendError(Exception):
    """Raised when the hosted API returns an error."""


class HttpBackend:
    """HTTP client that talks to a hosted Continuum API.

    Parameters
    ----------
    base_url:
        Base URL of the Continuum API (e.g. ``http://localhost:8787``).
    api_key:
        Optional API key for authentication.
    """

    def __init__(self, base_url: str, api_key: str | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    def _request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Send an HTTP request and return the parsed JSON response."""
        url = f"{self._base_url}{path}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"

        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            url, data=data, headers=self._headers(), method=method
        )
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode() if exc.fp else str(exc)
            raise HttpBackendError(
                f"HTTP {exc.code} from {method} {path}: {detail}"
            ) from exc

    # ------------------------------------------------------------------
    # StorageBackend-compatible interface
    # ------------------------------------------------------------------

    def commit(
        self,
        title: str,
        scope: str,
        decision_type: str,
        options: Optional[list[dict[str, Any]]] = None,
        rationale: Optional[str] = None,
        stakeholders: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        override_policy: Optional[str] = None,
        precedence: Optional[int] = None,
        supersedes: Optional[str] = None,
        key: Optional[str] = None,
        activate: bool = False,
    ) -> dict[str, Any]:
        """POST /commit — create a new decision."""
        body: dict[str, Any] = {
            "title": title,
            "scope": scope,
            "decision_type": decision_type,
            "rationale": rationale or "",
            "activate": activate,
        }
        if options is not None:
            body["options"] = options
        if stakeholders is not None:
            body["stakeholders"] = stakeholders
        if metadata is not None:
            body["metadata"] = metadata
        if override_policy is not None:
            body["override_policy"] = override_policy
        if precedence is not None:
            body["precedence"] = precedence
        if supersedes is not None:
            body["supersedes"] = supersedes
        if key is not None:
            body["key"] = key

        result = self._request("POST", "/commit", body=body)
        return result.get("decision", result)

    def get(self, decision_id: str) -> dict[str, Any]:
        """GET /decision/{id}."""
        result = self._request("GET", f"/decision/{decision_id}")
        return result.get("decision", result)

    def list_decisions(self, scope: str | None = None) -> list[dict[str, Any]]:
        """GET /decisions."""
        params = {"scope": scope} if scope else None
        result = self._request("GET", "/decisions", params=params)
        return result.get("decisions", [])

    def update_status(self, decision_id: str, new_status: str) -> dict[str, Any]:
        """PATCH /decision/{id}/status."""
        result = self._request(
            "PATCH",
            f"/decision/{decision_id}/status",
            body={"status": new_status},
        )
        return result.get("decision", result)

    def inspect(self, scope: str) -> dict[str, Any]:
        """GET /inspect?scope=...

        Returns ``{bindings, conflict_notes, items}``.
        """
        result = self._request("GET", "/inspect", params={"scope": scope})
        # Normalize: the API returns {binding, conflict_notes, items}
        bindings = result.get("bindings") or result.get("binding", [])
        return {
            "bindings": bindings,
            "conflict_notes": result.get("conflict_notes", []),
            "items": result.get("items", bindings),
        }

    def enforce(self, action: dict[str, Any], scope: str) -> dict[str, Any]:
        """POST /enforce."""
        result = self._request(
            "POST", "/enforce", body={"scope": scope, "action": action}
        )
        return result.get("enforcement", result)

    def resolve(
        self,
        query: str,
        scope: str,
        candidates: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        """POST /resolve."""
        body: dict[str, Any] = {"prompt": query, "scope": scope}
        if candidates is not None:
            body["candidates"] = candidates
        result = self._request("POST", "/resolve", body=body)
        return result.get("resolution", result)

    def supersede(
        self,
        old_id: str,
        new_title: str,
        rationale: Optional[str] = None,
        options: Optional[list[dict[str, Any]]] = None,
        stakeholders: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        override_policy: Optional[str] = None,
        precedence: Optional[int] = None,
        key: Optional[str] = None,
    ) -> dict[str, Any]:
        """POST /supersede."""
        body: dict[str, Any] = {"old_id": old_id, "new_title": new_title}
        if rationale is not None:
            body["rationale"] = rationale
        if options is not None:
            body["options"] = options
        if stakeholders is not None:
            body["stakeholders"] = stakeholders
        if metadata is not None:
            body["metadata"] = metadata
        if override_policy is not None:
            body["override_policy"] = override_policy
        if precedence is not None:
            body["precedence"] = precedence
        if key is not None:
            body["key"] = key
        result = self._request("POST", "/supersede", body=body)
        return result.get("decision", result)
