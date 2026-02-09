# Continuum Demo API

Thin FastAPI wrapper around `continuum-sdk` for the demo UI.

## Run

```bash
pip install -e .
uvicorn main:app --reload --port 8787
```

By default it uses the repo-local store at `./.continuum/` (repo root). Override with:

```bash
CONTINUUM_STORE="/path/to/.continuum" uvicorn demo.api.main:app --reload --port 8787
```

