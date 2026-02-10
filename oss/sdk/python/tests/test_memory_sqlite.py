"""Tests for SQLiteMemorySource."""

from __future__ import annotations

import pytest

from continuum.memory_sqlite import SQLiteMemorySource


@pytest.fixture()
def memory():
    """In-memory SQLite source."""
    with SQLiteMemorySource() as m:
        yield m


@pytest.fixture()
def file_memory(tmp_path):
    """File-backed SQLite source."""
    db = tmp_path / "signals.db"
    with SQLiteMemorySource(db) as m:
        yield m


# ------------------------------------------------------------------
# add_signal
# ------------------------------------------------------------------


class TestAddSignal:
    def test_basic_add(self, memory):
        sig = memory.add_signal(content="Team prefers REST", scope="repo:acme")
        assert sig["id"].startswith("sig_")
        assert sig["content"] == "Team prefers REST"
        assert sig["scope"] == "repo:acme"
        assert sig["timestamp"]
        assert sig["metadata"] == {}

    def test_add_with_metadata(self, memory):
        sig = memory.add_signal(
            content="Use PostgreSQL",
            scope="repo:acme",
            metadata={"source": "meeting", "confidence": 0.9},
        )
        assert sig["metadata"]["source"] == "meeting"
        assert sig["metadata"]["confidence"] == 0.9

    def test_add_with_custom_id(self, memory):
        sig = memory.add_signal(
            content="Custom signal",
            scope="repo:acme",
            signal_id="custom_001",
        )
        assert sig["id"] == "custom_001"

    def test_add_multiple(self, memory):
        for i in range(5):
            memory.add_signal(content=f"Signal {i}", scope="repo:acme")
        signals = memory.list_signals()
        assert len(signals) == 5


# ------------------------------------------------------------------
# search
# ------------------------------------------------------------------


class TestSearch:
    def test_search_by_content(self, memory):
        memory.add_signal(content="Team prefers REST over GraphQL", scope="repo:acme")
        memory.add_signal(content="Use Redis for caching", scope="repo:acme")
        memory.add_signal(content="REST endpoints should be versioned", scope="repo:acme")

        results = memory.search("REST")
        assert len(results) == 2
        contents = [r["content"] for r in results]
        assert "Use Redis for caching" not in contents

    def test_search_with_scope(self, memory):
        memory.add_signal(content="REST API pattern", scope="repo:frontend")
        memory.add_signal(content="REST API pattern", scope="repo:backend")

        results = memory.search("REST", scope="repo:frontend")
        assert len(results) == 1
        assert results[0]["scope"] == "repo:frontend"

    def test_search_case_insensitive(self, memory):
        memory.add_signal(content="Use REST APIs", scope="repo:acme")

        results = memory.search("rest")
        assert len(results) == 1

    def test_search_no_results(self, memory):
        memory.add_signal(content="Use Redis", scope="repo:acme")
        results = memory.search("GraphQL")
        assert results == []

    def test_search_limit(self, memory):
        for i in range(10):
            memory.add_signal(content=f"REST signal {i}", scope="repo:acme")

        results = memory.search("REST", limit=3)
        assert len(results) == 3

    def test_search_without_scope(self, memory):
        memory.add_signal(content="REST everywhere", scope="repo:a")
        memory.add_signal(content="REST here too", scope="repo:b")

        results = memory.search("REST")
        assert len(results) == 2


# ------------------------------------------------------------------
# list_signals
# ------------------------------------------------------------------


class TestListSignals:
    def test_list_empty(self, memory):
        assert memory.list_signals() == []

    def test_list_all(self, memory):
        memory.add_signal(content="A", scope="repo:x")
        memory.add_signal(content="B", scope="repo:y")
        assert len(memory.list_signals()) == 2

    def test_list_filtered(self, memory):
        memory.add_signal(content="A", scope="repo:x")
        memory.add_signal(content="B", scope="repo:y")
        result = memory.list_signals(scope="repo:x")
        assert len(result) == 1
        assert result[0]["content"] == "A"


# ------------------------------------------------------------------
# clear
# ------------------------------------------------------------------


class TestClear:
    def test_clear_all(self, memory):
        memory.add_signal(content="A", scope="repo:x")
        memory.add_signal(content="B", scope="repo:y")
        count = memory.clear()
        assert count == 2
        assert memory.list_signals() == []

    def test_clear_by_scope(self, memory):
        memory.add_signal(content="A", scope="repo:x")
        memory.add_signal(content="B", scope="repo:y")
        count = memory.clear(scope="repo:x")
        assert count == 1
        remaining = memory.list_signals()
        assert len(remaining) == 1
        assert remaining[0]["scope"] == "repo:y"


# ------------------------------------------------------------------
# persistence
# ------------------------------------------------------------------


class TestPersistence:
    def test_file_backed_persistence(self, tmp_path):
        db = tmp_path / "signals.db"

        # Write
        with SQLiteMemorySource(db) as m:
            m.add_signal(content="Persistent signal", scope="repo:test")

        # Read in new connection
        with SQLiteMemorySource(db) as m:
            results = m.search("Persistent")
            assert len(results) == 1
            assert results[0]["content"] == "Persistent signal"


# ------------------------------------------------------------------
# context manager
# ------------------------------------------------------------------


class TestContextManager:
    def test_context_manager(self):
        with SQLiteMemorySource() as m:
            m.add_signal(content="test", scope="x")
            assert len(m.list_signals()) == 1


# ------------------------------------------------------------------
# protocol compliance
# ------------------------------------------------------------------


class TestProtocol:
    def test_has_search_method(self, memory):
        assert hasattr(memory, "search")
        assert callable(memory.search)

    def test_search_signature_matches_protocol(self, memory):
        """Verify search accepts the protocol's keyword arguments."""
        result = memory.search("test", scope="x", limit=5)
        assert isinstance(result, list)


# ------------------------------------------------------------------
# Integration with ContinuumClient
# ------------------------------------------------------------------


class TestClientIntegration:
    def test_resolve_with_memory_source(self, tmp_path):
        from continuum.client import ContinuumClient

        memory = SQLiteMemorySource()
        memory.add_signal(
            content="Team previously chose REST over GraphQL",
            scope="repo:test",
        )

        client = ContinuumClient(
            storage_dir=str(tmp_path / ".continuum"),
            memory_source=memory,
        )
        result = client.resolve(query="REST", scope="repo:test")
        assert "status" in result

    def test_resolve_without_memory_source(self, tmp_path):
        """Client works fine without a memory source (backward compat)."""
        from continuum.client import ContinuumClient

        client = ContinuumClient(storage_dir=str(tmp_path / ".continuum"))
        result = client.resolve(query="anything", scope="repo:test")
        assert "status" in result
