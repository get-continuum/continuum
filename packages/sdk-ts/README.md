# Continuum TypeScript SDK

Install:

```bash
npm install @get-continuum/sdk
```

Quickstart:

```ts
import { Continuum } from "@get-continuum/sdk";

const continuum = new Continuum({
  baseUrl: "http://localhost:8000",
  workspaceId: "default",
  apiKey: process.env.CONTINUUM_API_KEY,
});

const out = await continuum.resolve({ query: "revenue by campaign", context: { team: "marketing" } });
console.log(out.status, out.resolved_metric);
```

