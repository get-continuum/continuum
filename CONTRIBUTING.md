# Contributing to Continuum

## Development setup

```bash
git clone https://github.com/get-continuum/continuum.git
cd continuum

pip install -e "oss/sdk/python[dev]"
pip install -e oss/cli

make test
make lint
```

## OSS boundary checklist

Before submitting a PR, ensure your changes in `oss/` do NOT introduce:

- [ ] Ambiguity scoring heuristics
- [ ] Decision compilation heuristics
- [ ] Risk scoring algorithms
- [ ] ML/NLP model weights or inference code
- [ ] LLM API calls

All of the above belong in `core/` (BSL-licensed).

## Pull request process

1. Create a feature branch from `main`
2. Make your changes
3. Ensure tests pass: `make test`
4. Ensure linting passes: `make lint`
5. Submit a PR and confirm the OSS boundary checklist

## Code style

- Python: formatted with `ruff`, type-checked with `mypy`
- All public APIs must have docstrings
- Tests required for new functionality
