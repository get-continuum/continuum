export type JsonObject = Record<string, unknown>;

export type IntentResolvedMetric = {
  metric_id: string;
  description: string;
  model: string;
  measure_name: string;
  domain: string;
};

export type IntentResolveResponse = {
  status: "resolved" | "ambiguous" | "no_match" | "error" | string;
  resolved_metric?: IntentResolvedMetric | null;
  candidates?: IntentResolvedMetric[] | null;
  confidence: number;
  reason: string;
};

export type ResolveContractResponse = {
  metric_id: string;
  base_version_id: number;
  applied_overlays: string[];
  resolved_snapshot: JsonObject;
  provenance: JsonObject;
};

export type MintTokenRequest = {
  user_id: string;
  roles?: string[];
  scopes?: string[];
  agent_id?: string | null;
  surface?: string | null;
  ttl_seconds?: number;
};

export type MintTokenResponse = {
  token: string;
  expires_in: number;
};

export type WhoAmIResponse = {
  workspace_id: string;
  auth_type: string;
  user_id?: string | null;
  roles: string[];
  scopes: string[];
  agent_id?: string | null;
  surface?: string | null;
};

