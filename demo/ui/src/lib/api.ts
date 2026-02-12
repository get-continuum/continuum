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

export async function patchJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${apiBase()}${path}`, {
    method: "PATCH",
    headers: { "content-type": "application/json", ...authHeaders() },
    body: JSON.stringify(body),
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

// -- Mining types ---------------------------------------------------------

export type EvidenceSpan = {
  source_type: string;
  source_ref: string;
  span_start: number;
  span_end: number;
  quote: string;
};

export type FactRecord = {
  id: string;
  category: string;
  statement: string;
  evidence: EvidenceSpan[];
  confidence: number;
};

export type DecisionCandidateRecord = {
  id: string;
  title: string;
  decision_type: string;
  scope_suggestion: string;
  risk: string;
  confidence: number;
  evidence: EvidenceSpan[];
  rationale: string;
  candidate_decision: Record<string, unknown>;
};

export type MineResultResponse = {
  facts: FactRecord[];
  decision_candidates: DecisionCandidateRecord[];
};

export function fetchMine(
  conversations: string[],
  scopeDefault: string,
  semanticContextRefs?: string[]
) {
  return postJson<MineResultResponse>("/mine", {
    conversations,
    scope_default: scopeDefault,
    semantic_context_refs: semanticContextRefs,
  });
}

export type ConflictNote = {
  type: string;
  winner_id?: string;
  loser_ids?: string[];
  explanation?: string;
  scores?: Record<string, number>;
};

export function fetchInspect(scope: string) {
  return getJson<{ binding: DecisionRecord[]; conflict_notes?: ConflictNote[] }>(
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

export function fetchCommitFromClarification(body: {
  chosen_option_id: string;
  scope: string;
  candidate_decision?: Record<string, unknown>;
  title?: string;
  decision_type?: string;
  rationale?: string;
}) {
  return postJson<{ decision: DecisionRecord; binding: DecisionRecord[] }>(
    "/commit_from_clarification",
    body
  );
}

export type GraphNode = {
  id: string;
  type: "decision" | "scope";
  data: Record<string, unknown>;
};

export type GraphEdge = {
  id: string;
  source: string;
  target: string;
  type: "applies_to" | "supersedes" | "overrides";
};

export function fetchGraph(scope?: string) {
  const qs = scope ? `?scope=${encodeURIComponent(scope)}` : "";
  return getJson<{ nodes: GraphNode[]; edges: GraphEdge[] }>(
    `/graph/decisions${qs}`
  );
}

export function fetchDecisions(scope?: string) {
  const qs = scope ? `?scope=${encodeURIComponent(scope)}` : "";
  return getJson<{ decisions: DecisionRecord[] }>(`/decisions${qs}`);
}

export function patchDecisionStatus(decisionId: string, status: string) {
  return patchJson<{ decision: DecisionRecord }>(
    `/decision/${decisionId}/status`,
    { status }
  );
}
