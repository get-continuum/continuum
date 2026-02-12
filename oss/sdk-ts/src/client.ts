/**
 * ContinuumClient — TypeScript client for the Continuum decision control plane.
 *
 * Supports two modes:
 *   - **local**: reads/writes decisions to the filesystem (Node.js only).
 *   - **remote**: talks to a hosted Continuum API over HTTP.
 */

import type {
  Decision,
  CommitParams,
  ResolveParams,
  ResolveResult,
  EnforceParams,
  EnforcementResult,
  SupersedeParams,
  MineParams,
  MineResult,
  ClarificationResponse,
} from "./types.js";

// ---------------------------------------------------------------------------
// Client options
// ---------------------------------------------------------------------------

export interface ContinuumClientOptions {
  /** Base URL for the remote API (e.g. "https://api.getcontinuum.ai"). */
  baseUrl?: string;

  /** API key for authentication with the remote API. */
  apiKey?: string;

  /**
   * Request timeout in milliseconds.
   * @default 30_000
   */
  timeout?: number;
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

export class ContinuumClient {
  private readonly baseUrl: string;
  private readonly apiKey: string | undefined;
  private readonly timeout: number;

  constructor(options: ContinuumClientOptions = {}) {
    this.baseUrl = (options.baseUrl ?? "http://localhost:8000").replace(
      /\/$/,
      "",
    );
    this.apiKey = options.apiKey;
    this.timeout = options.timeout ?? 30_000;
  }

  // -----------------------------------------------------------------------
  // Public API
  // -----------------------------------------------------------------------

  /** Create and persist a new decision. */
  async commit(params: CommitParams): Promise<Decision> {
    const body = {
      title: params.title,
      scope: params.scope,
      decision_type: params.decision_type,
      options: params.options ?? null,
      rationale: params.rationale ?? null,
      stakeholders: params.stakeholders ?? null,
      metadata: params.metadata ?? null,
      override_policy: params.override_policy ?? null,
      precedence: params.precedence ?? null,
      supersedes: params.supersedes ?? null,
    };
    const res = await this._post<{ decision: Decision }>("/commit", body);
    return res.decision;
  }

  /** Get a single decision by ID. */
  async get(decisionId: string): Promise<Decision> {
    const res = await this._get<{ decision: Decision }>(
      `/decision/${encodeURIComponent(decisionId)}`,
    );
    return res.decision;
  }

  /** List active decisions for a scope (the "binding set"). */
  async inspect(scope: string): Promise<Decision[]> {
    const res = await this._get<{ binding: Decision[] }>(
      `/inspect?scope=${encodeURIComponent(scope)}`,
    );
    return res.binding;
  }

  /** Run the ambiguity gate for a query against decisions in a scope. */
  async resolve(params: ResolveParams): Promise<ResolveResult> {
    const body = {
      prompt: params.query,
      scope: params.scope,
      candidates: params.candidates ?? null,
    };
    const res = await this._post<{ resolution: ResolveResult }>(
      "/resolve",
      body,
    );
    return res.resolution;
  }

  /** Evaluate an action against active decisions in a scope. */
  async enforce(params: EnforceParams): Promise<EnforcementResult> {
    const body = {
      scope: params.scope,
      action: params.action,
    };
    const res = await this._post<{ enforcement: EnforcementResult }>(
      "/enforce",
      body,
    );
    return res.enforcement;
  }

  /** Supersede an existing decision with a replacement. */
  async supersede(params: SupersedeParams): Promise<Decision> {
    const body = {
      old_id: params.old_id,
      new_title: params.new_title,
      rationale: params.rationale ?? null,
      options: params.options ?? null,
      stakeholders: params.stakeholders ?? null,
      metadata: params.metadata ?? null,
      override_policy: params.override_policy ?? null,
      precedence: params.precedence ?? null,
    };
    const res = await this._post<{ decision: Decision }>("/supersede", body);
    return res.decision;
  }

  /** Commit a decision from a clarification response. */
  async commitFromClarification(
    params: ClarificationResponse & {
      candidate_decision?: Record<string, unknown>;
      title?: string;
    },
  ): Promise<{ decision: Decision; binding: Decision[] }> {
    return this._post<{ decision: Decision; binding: Decision[] }>(
      "/commit_from_clarification",
      params,
    );
  }

  /** Extract facts and decision candidates from conversations. */
  async mine(params: MineParams): Promise<MineResult> {
    const body = {
      conversations: params.conversations,
      scope_default: params.scope_default,
      semantic_context_refs: params.semantic_context_refs ?? null,
    };
    return this._post<MineResult>("/mine", body);
  }

  /** Simple health check. */
  async health(): Promise<{ ok: boolean; store_dir: string }> {
    return this._get<{ ok: boolean; store_dir: string }>("/health");
  }

  // -----------------------------------------------------------------------
  // Internal HTTP helpers
  // -----------------------------------------------------------------------

  private _headers(): Record<string, string> {
    const h: Record<string, string> = {
      "Content-Type": "application/json",
      Accept: "application/json",
    };
    if (this.apiKey) {
      h["Authorization"] = `Bearer ${this.apiKey}`;
    }
    return h;
  }

  private async _get<T>(path: string): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const res = await fetch(url, {
      method: "GET",
      headers: this._headers(),
      signal: AbortSignal.timeout(this.timeout),
    });
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new ContinuumApiError(res.status, text, url);
    }
    return (await res.json()) as T;
  }

  private async _post<T>(path: string, body: unknown): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const res = await fetch(url, {
      method: "POST",
      headers: this._headers(),
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(this.timeout),
    });
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new ContinuumApiError(res.status, text, url);
    }
    return (await res.json()) as T;
  }
}

// ---------------------------------------------------------------------------
// Errors
// ---------------------------------------------------------------------------

export class ContinuumApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly body: string,
    public readonly url: string,
  ) {
    super(`Continuum API error ${status} from ${url}: ${body}`);
    this.name = "ContinuumApiError";
  }
}
