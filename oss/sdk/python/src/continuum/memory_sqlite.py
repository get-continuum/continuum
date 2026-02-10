"""SQLite-backed implementation of MemorySignalSource.

Uses only the Python standard library (sqlite3). No external dependencies.

Usage::

    from continuum.memory_sqlite import SQLiteMemorySource

    memory = SQLiteMemorySource("signals.db")
    memory.add_signal(scope="repo:acme", content="Team prefers REST over GraphQL")

    results = memory.search("REST", scope="repo:acme")
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


class SQLiteMemorySource:
    """A concrete ``MemorySignalSource`` backed by a SQLite database.

    Parameters
    ----------
    db_path:
        Path to the SQLite database file.  Defaults to ``:memory:`` for
        transient in-memory usage.
    """

    _CREATE_TABLE = """
        CREATE TABLE IF NOT EXISTS signals (
            id          TEXT PRIMARY KEY,
            scope       TEXT NOT NULL,
            content     TEXT NOT NULL,
            timestamp   TEXT NOT NULL,
            metadata    TEXT NOT NULL DEFAULT '{}'
        )
    """

    _CREATE_INDEX = """
        CREATE INDEX IF NOT EXISTS idx_signals_scope ON signals(scope)
    """

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self._db_path = str(db_path)
        self._conn = sqlite3.connect(self._db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(self._CREATE_TABLE)
        self._conn.execute(self._CREATE_INDEX)
        self._conn.commit()

    # ------------------------------------------------------------------
    # MemorySignalSource protocol
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        *,
        scope: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Return signals whose content contains *query* (case-insensitive).

        Parameters
        ----------
        query:
            Substring to match against signal content.
        scope:
            Optional scope filter (exact match).
        limit:
            Maximum number of results to return.
        """
        if scope:
            rows = self._conn.execute(
                "SELECT * FROM signals WHERE scope = ? AND content LIKE ? ORDER BY timestamp DESC LIMIT ?",
                (scope, f"%{query}%", limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM signals WHERE content LIKE ? ORDER BY timestamp DESC LIMIT ?",
                (f"%{query}%", limit),
            ).fetchall()

        return [self._row_to_dict(row) for row in rows]

    # ------------------------------------------------------------------
    # Write API (beyond the protocol)
    # ------------------------------------------------------------------

    def add_signal(
        self,
        content: str,
        scope: str,
        metadata: dict[str, Any] | None = None,
        signal_id: str | None = None,
    ) -> dict[str, Any]:
        """Persist a new memory signal.

        Parameters
        ----------
        content:
            The signal text content.
        scope:
            Scope this signal belongs to.
        metadata:
            Optional metadata dict.
        signal_id:
            Optional custom ID; auto-generated if omitted.

        Returns
        -------
        dict
            The persisted signal as a dict.
        """
        sid = signal_id or f"sig_{uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        meta_json = json.dumps(metadata or {})

        self._conn.execute(
            "INSERT INTO signals (id, scope, content, timestamp, metadata) VALUES (?, ?, ?, ?, ?)",
            (sid, scope, content, now, meta_json),
        )
        self._conn.commit()

        return {
            "id": sid,
            "scope": scope,
            "content": content,
            "timestamp": now,
            "metadata": metadata or {},
        }

    def clear(self, scope: str | None = None) -> int:
        """Delete signals, optionally filtered by scope.

        Parameters
        ----------
        scope:
            If provided, only delete signals for this scope.
            If ``None``, delete all signals.

        Returns
        -------
        int
            Number of signals deleted.
        """
        if scope:
            cursor = self._conn.execute("DELETE FROM signals WHERE scope = ?", (scope,))
        else:
            cursor = self._conn.execute("DELETE FROM signals")
        self._conn.commit()
        return cursor.rowcount

    def list_signals(self, scope: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        """List signals, optionally filtered by scope.

        Parameters
        ----------
        scope:
            Optional scope filter.
        limit:
            Maximum results.
        """
        if scope:
            rows = self._conn.execute(
                "SELECT * FROM signals WHERE scope = ? ORDER BY timestamp DESC LIMIT ?",
                (scope, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM signals ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()

        return [self._row_to_dict(row) for row in rows]

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "scope": row["scope"],
            "content": row["content"],
            "timestamp": row["timestamp"],
            "metadata": json.loads(row["metadata"]),
        }

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()

    def __enter__(self) -> SQLiteMemorySource:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
