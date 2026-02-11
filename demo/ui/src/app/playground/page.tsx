"use client";

import { useCallback, useEffect, useState } from "react";
import ScopePills from "@/components/ScopePills";
import AmbiguityCard from "@/components/AmbiguityCard";
import DecisionArtifact from "@/components/DecisionArtifact";
import InspectorPanel from "@/components/InspectorPanel";
import {
  fetchInspect,
  fetchResolve,
  fetchEnforce,
  fetchCommit,
  patchDecisionStatus,
} from "@/lib/api";
import type { DecisionRecord, ResolveResult, EnforcementResult } from "@/lib/api";

const DECISION_TYPES = [
  "interpretation",
  "standard",
  "guideline",
  "constraint",
];

export default function PlaygroundPage() {
  // -- Scope state --
  const [scopes, setScopes] = useState(["repo:continuum-demo"]);
  const primaryScope = scopes[0] || "";

  // -- Commit form state --
  const [title, setTitle] = useState("");
  const [formScope, setFormScope] = useState(primaryScope);
  const [decisionType, setDecisionType] = useState("interpretation");
  const [rationale, setRationale] = useState("");

  // -- Resolve / enforce state --
  const [resolvePrompt, setResolvePrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [binding, setBinding] = useState<DecisionRecord[]>([]);
  const [lastResolution, setLastResolution] = useState<ResolveResult | null>(null);
  const [lastEnforcement, setLastEnforcement] = useState<EnforcementResult | null>(null);
  const [selectedDecision, setSelectedDecision] = useState<DecisionRecord | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  // Keep form scope in sync when primary scope changes
  useEffect(() => {
    setFormScope(primaryScope);
  }, [primaryScope]);

  const refreshInspector = useCallback(async () => {
    if (!primaryScope) return;
    try {
      const data = await fetchInspect(primaryScope);
      setBinding(data.binding ?? []);
    } catch {
      /* ignore */
    }
  }, [primaryScope]);

  useEffect(() => {
    void refreshInspector();
  }, [refreshInspector]);

  // -- Commit --
  const handleCommit = async () => {
    if (!title.trim() || !formScope.trim()) return;
    setLoading(true);
    setStatusMessage(null);
    try {
      const data = await fetchCommit({
        title: title.trim(),
        scope: formScope.trim(),
        decision_type: decisionType,
        rationale: rationale.trim() || `Decision: ${title.trim()}`,
        activate: true,
      });
      setStatusMessage(`Decision committed: ${data.decision.title} (${data.decision.id})`);
      setTitle("");
      setRationale("");
      await refreshInspector();
    } catch (e: unknown) {
      setStatusMessage(`Commit failed: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setLoading(false);
    }
  };

  // -- Resolve --
  const handleResolve = async () => {
    const p = resolvePrompt.trim();
    if (!p) return;
    setLoading(true);
    setLastEnforcement(null);
    setStatusMessage(null);
    try {
      const data = await fetchResolve(p, primaryScope);
      setLastResolution(data.resolution);
      if (data.resolution.status === "resolved") {
        setStatusMessage(
          `Resolved by prior decision: ${
            (data.resolution as { matched_decision_id?: string }).matched_decision_id ?? "unknown"
          }`
        );
      } else {
        setStatusMessage("Ambiguity Gate: needs clarification.");
      }
    } catch (e: unknown) {
      setStatusMessage(`Error: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setLoading(false);
      await refreshInspector();
    }
  };

  // -- Enforce --
  const handleEnforce = async () => {
    const p = resolvePrompt.trim();
    setLoading(true);
    setStatusMessage(null);
    try {
      const data = await fetchEnforce(primaryScope, {
        type: "code_change",
        description: p || "Generic action to enforce",
      });
      setLastEnforcement(data.enforcement);
      setStatusMessage(
        `Enforcement verdict: ${data.enforcement.verdict} (${data.enforcement.reason})`
      );
    } catch (e: unknown) {
      setStatusMessage(`Error: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setLoading(false);
      await refreshInspector();
    }
  };

  // -- Commit from ambiguity card --
  const promoteInterpretation = async (
    selectedId: string,
    selectedTitle: string,
    scope: string
  ) => {
    setLoading(true);
    setStatusMessage(null);
    try {
      await fetchCommit({
        title: selectedTitle,
        scope,
        decision_type: "interpretation",
        rationale: `Decision: ${selectedTitle}`,
        metadata: { selected_option_id: selectedId },
        activate: true,
      });
      setLastResolution(null);
      setStatusMessage(`Decision committed: ${selectedTitle}`);
      await refreshInspector();
    } catch (e: unknown) {
      setStatusMessage(`Commit failed: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setLoading(false);
    }
  };

  // -- Supersede from inspector --
  const handleSupersede = (decision: DecisionRecord) => {
    const enforcement = decision.enforcement;
    setTitle(`${decision.title} (v2)`);
    setFormScope(enforcement?.scope || primaryScope);
    setDecisionType(enforcement?.decision_type || "interpretation");
    setRationale(`Supersedes: ${decision.id} — ${decision.title}`);
    setSelectedDecision(null);
    setStatusMessage(`Pre-filled form to supersede "${decision.title}". Edit and commit.`);
    // Scroll to top
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  // -- Archive from inspector --
  const handleArchive = async (decision: DecisionRecord) => {
    setLoading(true);
    setStatusMessage(null);
    try {
      await patchDecisionStatus(decision.id, "archived");
      setStatusMessage(`Archived: ${decision.title}`);
      setSelectedDecision(null);
      await refreshInspector();
    } catch (e: unknown) {
      setStatusMessage(`Archive failed: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-full">
      {/* Main content */}
      <div className="flex-1 overflow-auto p-6">
        <h1 className="text-lg font-semibold">Playground</h1>

        {/* Scope pills */}
        <div className="mt-4">
          <ScopePills scopes={scopes} onChange={setScopes} />
        </div>

        {/* ---- Commit Form ---- */}
        <div className="mt-6 rounded-xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
          <h2 className="text-sm font-semibold text-zinc-700 dark:text-zinc-300">
            Commit a Decision
          </h2>

          <div className="mt-3 grid grid-cols-2 gap-3">
            {/* Title */}
            <div className="col-span-2">
              <label className="text-xs font-medium text-zinc-500">Title</label>
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Use bullet-point responses"
                className="mt-1 w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-teal-500/30 dark:border-zinc-800 dark:bg-zinc-950"
              />
            </div>

            {/* Scope */}
            <div>
              <label className="text-xs font-medium text-zinc-500">Scope</label>
              <input
                value={formScope}
                onChange={(e) => setFormScope(e.target.value)}
                placeholder="e.g. repo:my-app"
                className="mt-1 w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-teal-500/30 dark:border-zinc-800 dark:bg-zinc-950"
              />
            </div>

            {/* Decision type */}
            <div>
              <label className="text-xs font-medium text-zinc-500">Type</label>
              <select
                value={decisionType}
                onChange={(e) => setDecisionType(e.target.value)}
                className="mt-1 w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-teal-500/30 dark:border-zinc-800 dark:bg-zinc-950"
              >
                {DECISION_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>

            {/* Rationale */}
            <div className="col-span-2">
              <label className="text-xs font-medium text-zinc-500">
                Rationale <span className="text-zinc-400">(optional)</span>
              </label>
              <textarea
                value={rationale}
                onChange={(e) => setRationale(e.target.value)}
                rows={2}
                placeholder="Why was this decided?"
                className="mt-1 w-full resize-none rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-teal-500/30 dark:border-zinc-800 dark:bg-zinc-950"
              />
            </div>
          </div>

          <button
            onClick={handleCommit}
            disabled={loading || !title.trim()}
            className="mt-3 rounded-lg bg-teal-600 px-5 py-2 text-sm font-medium text-white hover:bg-teal-700 disabled:opacity-50"
          >
            Commit Decision
          </button>
        </div>

        {/* ---- Resolve / Enforce Section ---- */}
        <div className="mt-6 rounded-xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
          <h2 className="text-sm font-semibold text-zinc-700 dark:text-zinc-300">
            Resolve &amp; Enforce
          </h2>
          <p className="mt-1 text-xs text-zinc-400">
            Test how your decisions respond to queries and actions.
          </p>

          <div className="mt-3">
            <input
              value={resolvePrompt}
              onChange={(e) => setResolvePrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) void handleResolve();
              }}
              placeholder="Ask anything... e.g. Make it production-ready"
              className="w-full rounded-lg border border-zinc-200 bg-white px-4 py-2.5 text-sm shadow-sm outline-none focus:ring-2 focus:ring-teal-500/30 dark:border-zinc-800 dark:bg-zinc-950"
            />
          </div>

          <div className="mt-3 flex gap-2">
            <button
              onClick={handleResolve}
              disabled={loading || !resolvePrompt.trim()}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              Resolve
            </button>
            <button
              onClick={handleEnforce}
              disabled={loading}
              className="rounded-lg border border-zinc-200 bg-white px-4 py-2 text-sm font-medium hover:bg-zinc-50 disabled:opacity-50 dark:border-zinc-800 dark:bg-zinc-950 dark:hover:bg-zinc-900"
            >
              Enforce
            </button>
          </div>
        </div>

        {/* Status */}
        {statusMessage && (
          <div className="mt-4 rounded-lg border border-zinc-200 bg-zinc-50 p-3 text-sm text-zinc-700 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300">
            {statusMessage}
          </div>
        )}

        {/* Ambiguity card */}
        {lastResolution && lastResolution.status === "needs_clarification" && (
          <div className="mt-4">
            <AmbiguityCard
              result={lastResolution}
              prompt={resolvePrompt}
              loading={loading}
              onCommit={promoteInterpretation}
              scopes={scopes}
            />
          </div>
        )}

        {/* Enforcement result */}
        {lastEnforcement && (
          <div
            className={[
              "mt-4 rounded-xl border p-4 text-sm",
              lastEnforcement.verdict === "block"
                ? "border-red-200 bg-red-50 dark:border-red-900/40 dark:bg-red-950/30"
                : lastEnforcement.verdict === "confirm"
                ? "border-amber-200 bg-amber-50 dark:border-amber-900/40 dark:bg-amber-950/30"
                : "border-emerald-200 bg-emerald-50 dark:border-emerald-900/40 dark:bg-emerald-950/30",
            ].join(" ")}
          >
            <div className="text-xs font-semibold">Enforcement Result</div>
            <div className="mt-1 flex items-center gap-2">
              <span
                className={[
                  "rounded-full px-2 py-0.5 text-[10px] font-bold uppercase",
                  lastEnforcement.verdict === "block"
                    ? "bg-red-200 text-red-900 dark:bg-red-900/50 dark:text-red-300"
                    : lastEnforcement.verdict === "confirm"
                    ? "bg-amber-200 text-amber-900 dark:bg-amber-900/50 dark:text-amber-300"
                    : "bg-emerald-200 text-emerald-900 dark:bg-emerald-900/50 dark:text-emerald-300",
                ].join(" ")}
              >
                {lastEnforcement.verdict}
              </span>
              <span className="text-xs text-zinc-600 dark:text-zinc-400">
                {lastEnforcement.reason}
              </span>
            </div>
          </div>
        )}

        {/* Decision Artifact */}
        {selectedDecision && (
          <div className="mt-4">
            <DecisionArtifact
              decision={selectedDecision}
              onClose={() => setSelectedDecision(null)}
              onSupersede={() => handleSupersede(selectedDecision)}
              onArchive={() => handleArchive(selectedDecision)}
            />
          </div>
        )}
      </div>

      {/* Inspector panel */}
      <InspectorPanel
        decisions={binding}
        scopes={scopes}
        onSelectDecision={setSelectedDecision}
        onSupersede={handleSupersede}
        onArchive={handleArchive}
      />
    </div>
  );
}
