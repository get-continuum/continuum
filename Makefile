# Continuum OSS Monorepo
# Core engine lives in the separate continuum-core repo (BSL-1.1).
# This Makefile covers only the OSS layer (Apache-2.0).

.PHONY: lint test typecheck install install-dev clean all

all: lint typecheck test

install:
	pip install -e oss/sdk/python
	pip install -e oss/cli

install-dev:
	pip install -e "oss/sdk/python[dev]"
	pip install -e oss/cli

lint:
	ruff check oss/

typecheck:
	mypy oss/sdk/python/src/continuum/

test:
	pytest oss/contracts/tests/ oss/sdk/python/tests/ oss/cli/tests/ oss/mcp-server/tests/ -v

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
