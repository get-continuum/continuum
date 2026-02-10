/**
 * TypeScript types for the Continuum decision control plane.
 *
 * These mirror the Python SDK models and JSON Schema contracts so both
 * ecosystems share the same vocabulary.
 */

// ---------------------------------------------------------------------------
// Enums
// ---------------------------------------------------------------------------

/** Lifecycle status of a decision. */
export type DecisionStatus = "draft" | "active" | "superseded" | "archived";

/** Classification of the decision. */
export type DecisionType =
  | "interpretation"
  | "rejection"
  | "preference"
  | "behavior_rule";

/** How overrides are handled. */
export type OverridePolicy = "invalid_by_default" | "warn" | "allow";

/** Classification of an action being evaluated. */
export type ActionType =
  | "code_change"
  | "migration"
  | "api_break"
  | "deployment"
  | "config_change"
  | "generic";

/** Outcome of enforcement evaluation. */
export type EnforcementVerdict = "allow" | "block" | "confirm" | "override";

/** Resolution status from the ambiguity gate. */
export type ResolveStatus = "resolved" | "needs_clarification";

// ---------------------------------------------------------------------------
// Core models
// ---------------------------------------------------------------------------

/** An option considered during a decision. */
export interface Option {
  id: string;
  title: string;
  selected: boolean;
  rejected_reason?: string | null;
}

/** Contextual information about when/why a decision was made. */
export interface DecisionContext {
  trigger: string;
  source: string;
  timestamp: string; // ISO 8601
  actor?: string | null;
}

/** Enforcement rules for a decision. */
export interface Enforcement {
  scope: string;
  decision_type: DecisionType;
  supersedes?: string | null;
  precedence?: number | null;
  override_policy: OverridePolicy;
}

/** Core decision record — the atomic unit of institutional knowledge. */
export interface Decision {
  id: string;
  version: number;
  status: DecisionStatus;
  title: string;
  rationale?: string | null;
  options_considered: Option[];
  context?: DecisionContext | null;
  enforcement?: Enforcement | null;
  stakeholders: string[];
  metadata: Record<string, unknown>;
  created_at: string; // ISO 8601
  updated_at: string; // ISO 8601
}

// ---------------------------------------------------------------------------
// Enforcement types
// ---------------------------------------------------------------------------

/** An action to be evaluated against enforcement rules. */
export interface Action {
  type: ActionType;
  description: string;
  scope: string;
  metadata?: Record<string, unknown>;
}

/** Result of evaluating an action against decisions. */
export interface EnforcementResult {
  verdict: EnforcementVerdict;
  reason: string;
  matched_decisions: string[];
  required_confirmations: string[];
}

// ---------------------------------------------------------------------------
// Resolve / ambiguity-gate types
// ---------------------------------------------------------------------------

/** A candidate option supplied by the caller. */
export interface CandidateOption {
  id: string;
  title: string;
  source?: string;
  confidence?: number;
}

/** A request for the caller to clarify intent. */
export interface ClarificationRequest {
  question: string;
  candidates: CandidateOption[];
  context?: Record<string, unknown>;
}

/** Result of the resolve operation. */
export interface ResolveResult {
  status: ResolveStatus;
  resolved_context?: Record<string, unknown> | null;
  clarification?: ClarificationRequest | null;
  matched_decision_id?: string | null;
}

// ---------------------------------------------------------------------------
// Client request/response types
// ---------------------------------------------------------------------------

/** Parameters for committing a new decision. */
export interface CommitParams {
  title: string;
  scope: string;
  decision_type: DecisionType;
  options?: Array<Omit<Option, "id"> & { id?: string }>;
  rationale?: string;
  stakeholders?: string[];
  metadata?: Record<string, unknown>;
  override_policy?: OverridePolicy;
  precedence?: number;
  supersedes?: string;
}

/** Parameters for resolving a query. */
export interface ResolveParams {
  query: string;
  scope: string;
  candidates?: CandidateOption[];
}

/** Parameters for enforcing an action. */
export interface EnforceParams {
  action: Action;
  scope: string;
}

/** Parameters for superseding a decision. */
export interface SupersedeParams {
  old_id: string;
  new_title: string;
  rationale?: string;
  options?: Array<Omit<Option, "id"> & { id?: string }>;
  stakeholders?: string[];
  metadata?: Record<string, unknown>;
  override_policy?: OverridePolicy;
  precedence?: number;
}
