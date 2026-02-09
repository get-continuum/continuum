"""Shared pytest fixtures for Continuum SDK tests."""

from __future__ import annotations

import pytest
from pathlib import Path


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    """Provide a temporary directory for client storage during tests."""
    return tmp_path
