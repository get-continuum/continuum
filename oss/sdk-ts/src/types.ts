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

/** Who issued the decision. */
export type IssuerType = "human" | "agent" | "system";

/** Authority level of the issuer. */
export type AuthorityLevel = "admin" | "lead" | "member";

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
  issuer_type?: IssuerType | null;
  authority?: AuthorityLevel | null;
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
  impact_preview?: string | null;
}

/** A request for the caller to clarify intent. */
export interface ClarificationRequest {
  question: string;
  candidates: CandidateOption[];
  context?: Record<string, unknown>;
  suggested_scope?: string | null;
  candidate_decision?: Record<string, unknown> | null;
}

/** A response to a clarification request. */
export interface ClarificationResponse {
  chosen_option_id: string;
  scope: string;
  commit?: boolean;
}

/** Result of the resolve operation. */
export interface ResolveResult {
  status: ResolveStatus;
  resolved_context?: Record<string, unknown> | null;
  clarification?: ClarificationRequest | null;
  matched_decision_id?: string | null;
}

// ---------------------------------------------------------------------------
// Mining types
// ---------------------------------------------------------------------------

/** Risk classification for a mined decision candidate. */
export type RiskLevel = "low" | "medium" | "high";

/** A span of text that supports a fact or candidate. */
export interface EvidenceSpan {
  source_type: string;
  source_ref: string;
  span_start: number;
  span_end: number;
  quote: string;
}

/** An extracted fact from a conversation. */
export interface Fact {
  id: string;
  category: string;
  statement: string;
  evidence: EvidenceSpan[];
  confidence: number;
}

/** A candidate decision ready for human review or auto-commit. */
export interface DecisionCandidate {
  id: string;
  title: string;
  decision_type: string;
  scope_suggestion: string;
  risk: RiskLevel;
  confidence: number;
  evidence: EvidenceSpan[];
  rationale: string;
  candidate_decision: Record<string, unknown>;
}

/** Result of the mining pipeline. */
export interface MineResult {
  facts: Fact[];
  decision_candidates: DecisionCandidate[];
}

/** Parameters for mining conversations. */
export interface MineParams {
  conversations: string[];
  scope_default: string;
  semantic_context_refs?: string[];
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
