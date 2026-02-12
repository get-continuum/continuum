/**
 * @get-continuum/sdk — TypeScript SDK for the Continuum decision control plane.
 *
 * @example
 * ```ts
 * import { ContinuumClient } from "@get-continuum/sdk";
 *
 * const client = new ContinuumClient({ baseUrl: "http://localhost:8000" });
 *
 * const decision = await client.commit({
 *   title: "Revenue means net_revenue",
 *   scope: "org:acme",
 *   decision_type: "interpretation",
 *   rationale: "Finance team confirmed net_revenue is the standard metric.",
 * });
 *
 * const bindings = await client.inspect("org:acme");
 * ```
 */

// Types — re-exported from contracts
export type {
  // Enums
  DecisionStatus,
  DecisionType,
  OverridePolicy,
  ActionType,
  EnforcementVerdict,
  ResolveStatus,
  // Core models
  Option,
  DecisionContext,
  Enforcement,
  Decision,
  // Enforcement
  Action,
  EnforcementResult,
  // Resolve
  CandidateOption,
  ClarificationRequest,
  ResolveResult,
  // Client params
  CommitParams,
  ResolveParams,
  EnforceParams,
  SupersedeParams,
  MineParams,
  // Mining types
  RiskLevel,
  EvidenceSpan,
  Fact,
  DecisionCandidate,
  MineResult,
} from "./types.js";

// Client
export { ContinuumClient, ContinuumApiError } from "./client.js";
export type { ContinuumClientOptions } from "./client.js";
