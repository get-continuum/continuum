import { AuthError, HttpError, ResolveError } from "./errors.js";
import type {
  IntentResolveResponse,
  JsonObject,
  MintTokenRequest,
  MintTokenResponse,
  ResolveContractResponse,
  WhoAmIResponse,
} from "./types.js";

export type ContinuumClientOptions = {
  /**
   * Base URL for Continuum Core API (example: https://api.getcontinuum.ai)
   */
  baseUrl?: string;
  /**
   * Workspace id used as `?workspace_id=...` query param.
   */
  workspaceId?: string;
  /**
   * Workspace key (admin/ingestion channel). Sent as `Authorization: Bearer ...`.
   */
  apiKey?: string;
  /**
   * User JWT (runtime channel). Sent as `Authorization: Bearer ...`.
   */
  userToken?: string;
  /**
   * Custom fetch (useful for edge runtimes or testing).
   */
  fetch?: typeof fetch;
};

type AuthMode = "workspace" | "user" | "either" | "none";

export class Continuum {
  private baseUrl: string;
  private workspaceId: string;
  private apiKey: string | undefined;
  private userToken: string | undefined;
  private fetchImpl: typeof fetch;

  constructor(opts: ContinuumClientOptions = {}) {
    this.baseUrl = (opts.baseUrl ?? "http://localhost:8000").replace(/\/+$/, "");
    this.workspaceId = opts.workspaceId ?? "default";
    this.apiKey = opts.apiKey;
    this.userToken = opts.userToken;
    this.fetchImpl = opts.fetch ?? fetch;
  }

  setApiKey(apiKey: string | undefined): void {
    this.apiKey = apiKey;
  }

  setUserToken(userToken: string | undefined): void {
    this.userToken = userToken;
  }

  setWorkspaceId(workspaceId: string): void {
    this.workspaceId = workspaceId;
  }

  private headers(auth: AuthMode): HeadersInit {
    if (auth === "none") return {};
    const token =
      auth === "workspace"
        ? this.apiKey
        : auth === "user"
          ? this.userToken
          : this.userToken ?? this.apiKey;

    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  private async parseErrorMessage(r: Response): Promise<string> {
    try {
      const j = (await r.json()) as unknown;
      if (j && typeof j === "object" && "detail" in j) {
        const detail = (j as any).detail;
        if (typeof detail === "string" && detail.trim()) return detail;
      }
    } catch {
      // ignore
    }
    try {
      const t = await r.text();
      if (t?.trim()) return t;
    } catch {
      // ignore
    }
    return "request failed";
  }

  private async request<T>(
    method: string,
    path: string,
    {
      auth,
      query,
      body,
      kind,
    }: {
      auth: AuthMode;
      query?: Record<string, string | number | boolean | undefined>;
      body?: unknown;
      kind?: "resolve_intent" | "resolve_contract" | "other";
    },
  ): Promise<T> {
    const url = new URL(`${this.baseUrl}${path}`);
    url.searchParams.set("workspace_id", this.workspaceId);
    for (const [k, v] of Object.entries(query ?? {})) {
      if (v === undefined) continue;
      url.searchParams.set(k, String(v));
    }

    let r: Response;
    try {
      const init: RequestInit = {
        method,
        headers: {
          "content-type": "application/json",
          ...this.headers(auth),
        },
      };
      if (body !== undefined) init.body = JSON.stringify(body);

      r = await this.fetchImpl(url.toString(), init);
    } catch (e: any) {
      throw new HttpError({
        statusCode: 0,
        message: String(e?.message ?? e ?? "network error"),
        url: url.toString(),
      });
    }

    if (!r.ok) {
      const msg = await this.parseErrorMessage(r);
      const status = r.status ?? 0;
      const errInit: {
        statusCode: number;
        message: string;
        url: string;
        responseText?: string;
      } = {
        statusCode: status,
        message: msg,
        url: url.toString(),
      };
      try {
        errInit.responseText = await r.text();
      } catch {
        // ignore
      }

      if (status === 401 || status === 403) throw new AuthError(errInit);
      if (kind === "resolve_intent" || kind === "resolve_contract") throw new ResolveError(errInit);
      throw new HttpError(errInit);
    }

    try {
      return (await r.json()) as T;
    } catch (e: any) {
      throw new HttpError({
        statusCode: r.status ?? 0,
        message: `invalid JSON response: ${String(e?.message ?? e)}`,
        url: url.toString(),
      });
    }
  }

  /**
   * Resolve an ambiguous query into a grounded metric meaning.
   * Calls: POST /metrics/resolve_intent
   */
  async resolve(params: { query: string; context?: JsonObject }): Promise<IntentResolveResponse> {
    return this.request<IntentResolveResponse>("POST", "/metrics/resolve_intent", {
      auth: "either",
      body: { query: params.query, context: params.context ?? {} },
      kind: "resolve_intent",
    });
  }

  /**
   * Resolve a specific metric to a concrete contract state.
   * Calls: POST /metrics/{metric_id}/resolve
   */
  async resolveMetric(metricId: string, params: { context?: JsonObject } = {}): Promise<ResolveContractResponse> {
    return this.request<ResolveContractResponse>("POST", `/metrics/${encodeURIComponent(metricId)}/resolve`, {
      auth: "either",
      body: { context: params.context ?? {} },
      kind: "resolve_contract",
    });
  }

  /**
   * Mint a short-lived user JWT using a workspace key.
   * Calls: POST /auth/token
   */
  async mintUserToken(req: MintTokenRequest): Promise<MintTokenResponse> {
    return this.request<MintTokenResponse>("POST", "/auth/token", {
      auth: "workspace",
      body: req,
      kind: "other",
    });
  }

  /**
   * Inspect auth context for the current token.
   * Calls: GET /auth/whoami
   */
  async whoami(): Promise<WhoAmIResponse> {
    return this.request<WhoAmIResponse>("GET", "/auth/whoami", { auth: "either", kind: "other" });
  }
}

