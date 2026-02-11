/**
 * Typed API client for the Continuum backend.
 * Automatically includes auth headers when a token is available.
 */

function apiBase(): string {
  return process.env.NEXT_PUBLIC_CONTINUUM_API || "http://localhost:8787";
}

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("continuum_token");
}

function authHeaders(): Record<string, string> {
  const token = getToken();
  if (token) {
    return { Authorization: `Bearer ${token}` };
  }
  return {};
}

export async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${apiBase()}${path}`, {
    method: "POST",
    headers: { "content-type": "application/json", ...authHeaders() },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return (await res.json()) as T;
}

export async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${apiBase()}${path}`, {
    cache: "no-store",
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error(await res.text());
  return (await res.json()) as T;
}

export async function deleteJson<T>(path: string): Promise<T> {
  const res = await fetch(`${apiBase()}${path}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error(await res.text());
  return (await res.json()) as T;
}

// -- Typed wrappers -------------------------------------------------------

export type DecisionRecord = {
  id: string;
  title: string;
  status: string;
  version?: number;
  rationale?: string;
  options_considered?: Array<{
    id: string;
    title: string;
    selected: boolean;
    rejected_reason?: string;
  }>;
  enforcement?: {
    scope?: string;
    decision_type?: string;
    supersedes?: string;
    override_policy?: string;
  };
  metadata?: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
};

export type ResolveResult =
  | {
      status: "resolved";
      resolved_context?: unknown;
      matched_decision_id?: string;
    }
  | {
      status: "needs_clarification";
      clarification?: {
        question: string;
        candidates: Array<{ id: string; title: string }>;
      };
    };

export type EnforcementResult = {
  verdict: string;
  reason: string;
  matched_decisions?: string[];
  required_confirmations?: string[];
};

export type ApiKey = {
  id: string;
  name: string;
  created_at: string;
  hash_prefix?: string;
};

export function fetchInspect(scope: string) {
  return getJson<{ binding: DecisionRecord[] }>(
    `/inspect?scope=${encodeURIComponent(scope)}`
  );
}

export function fetchResolve(
  prompt: string,
  scope: string,
  candidates?: Array<{ id: string; title: string }>
) {
  return postJson<{ resolution: ResolveResult }>("/resolve", {
    prompt,
    scope,
    candidates,
  });
}

export function fetchEnforce(
  scope: string,
  action: Record<string, unknown>
) {
  return postJson<{ enforcement: EnforcementResult }>("/enforce", {
    scope,
    action,
  });
}

export function fetchCommit(body: Record<string, unknown>) {
  return postJson<{ decision: DecisionRecord }>("/commit", body);
}

export function fetchSupersede(body: Record<string, unknown>) {
  return postJson<{ decision: DecisionRecord }>("/supersede", body);
}

export function fetchApiKeys() {
  return getJson<{ keys: ApiKey[] }>("/api-keys");
}

export function createApiKey(name: string) {
  return postJson<{ key_id: string; raw_key: string; name: string }>(
    "/api-keys",
    { name }
  );
}

export function revokeApiKey(keyId: string) {
  return deleteJson<{ deleted: boolean }>(`/api-keys/${keyId}`);
}
