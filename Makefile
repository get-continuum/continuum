.PHONY: lint test typecheck install install-dev clean all

all: lint typecheck test

install:
	pip install -e oss/sdk/python
	pip install -e oss/cli

install-dev:
	pip install -e "oss/sdk/python[dev]"
	pip install -e oss/cli

install-engine:
	pip install -e "core[dev]"

lint:
	ruff check oss/ core/src/ || true

typecheck:
	mypy oss/sdk/python/src/continuum/

test:
	pytest oss/contracts/tests/ oss/sdk/python/tests/ -v

test-engine:
	pytest core/tests/ -v

test-all: test test-engine

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
