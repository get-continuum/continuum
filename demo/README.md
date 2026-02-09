# Continuum Demo (UI + API)

This folder contains a lightweight, Continuum-native demo:

- `demo/api/`: FastAPI wrapper around the Python SDK
- `demo/ui/`: Next.js UI (chat + Decision Inspector)

Both read/write a **repo-local store** (by default `./.continuum/` at the repo root), so the portability story is real.

## Prereqs

- Python 3.10+
- Node.js + npm

## Quickstart (2 terminals)

### Terminal A — API

```bash
cd demo/api
python3 -m pip install -e .
uvicorn main:app --reload --port 8787
```

By default the API uses the repo-local store at `./.continuum/`.

To point at a different store:

```bash
CONTINUUM_STORE="/path/to/.continuum" uvicorn main:app --reload --port 8787
```

Sanity check:

```bash
curl -s http://localhost:8787/health
```

### Terminal B — UI

```bash
cd demo/ui
npm install
NEXT_PUBLIC_CONTINUUM_API="http://localhost:8787" npm run dev
```

Open `http://localhost:3000`.

## What the UI is calling

The UI calls 1:1 endpoints that mirror the MCP surface:

- `GET /inspect?scope=...` (binding set)
- `POST /resolve`
- `POST /enforce`
- `POST /commit`
- `POST /supersede`
- `GET /decision/{id}`

## Recordable demo script (2–3 minutes)

1) **Start clean**
- Ensure `./.continuum/` doesn’t exist (or point `CONTINUUM_STORE` at an empty dir).
- Refresh the page: inspector should be empty.

2) **Seed a “hard” constraint**
- Click **Seed demo decisions**.
- In the inspector, you should see an active rejection decision: “Reject full rewrites …”.

3) **Show the Ambiguity Gate**
- Send: **Make it production-ready**
- The Ambiguity Gate appears with two options.

4) **Promote to decision**
- Click one of the options.
- Inspector now shows an active interpretation decision: `production-ready`.

5) **Prove “sticky resolution”**
- Send: **Make it production-ready** again.
- This time it should resolve without gating (it’s covered by the stored decision).

6) **Prove enforcement**
- Click **Try “full rewrite”**.
- You should see an enforcement verdict (typically `block` by default) with a reason referencing the rejection decision.

7) **Prove supersession + diff story**
- Click **Supersede “production-ready”**.
- Inspector should show the new active decision, with `supersedes` pointing at the prior one (v1 → v2).

## Troubleshooting

- **UI loads but actions fail**: confirm the API is running on `8787` and `NEXT_PUBLIC_CONTINUUM_API` matches it.
- **CORS issues**: the API enables permissive CORS for demo purposes.
- **No decisions appear**: make sure the API’s `CONTINUUM_STORE` points to the same store you expect (default is repo root `./.continuum/`).

