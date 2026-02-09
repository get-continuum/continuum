Continuum demo UI (chat + decision inspector).

## Getting Started

### 1) Start the demo API

From the repo root:

```bash
cd demo/api
python3 -m pip install -e .
uvicorn main:app --reload --port 8787
```

The API reads/writes the repo-local store at `./.continuum/` by default.

### 2) Start the UI

```bash
cd demo/ui
npm install
NEXT_PUBLIC_CONTINUUM_API="http://localhost:8787" npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

The main UI lives in `src/app/page.tsx`.

## Demo Flow

- Click **Seed demo decisions** (creates “Reject full rewrites …” in the store)
- Send **Make it production-ready**
- Pick an option in the **Ambiguity Gate** (promotes to an interpretation decision)
- Send the same prompt again (should resolve without gating)
- Click **Try “full rewrite”** (should block/confirm depending on override policy)
- Click **Supersede “production-ready”** (v1 → v2)
