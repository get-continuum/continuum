"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import ScopePills from "@/components/ScopePills";
import AmbiguityCard from "@/components/AmbiguityCard";
import DecisionArtifact from "@/components/DecisionArtifact";
import InspectorPanel from "@/components/InspectorPanel";
import {
  fetchInspect,
  fetchResolve,
  fetchEnforce,
  fetchCommit,
  fetchSupersede,
} from "@/lib/api";
import type { DecisionRecord, ResolveResult, EnforcementResult } from "@/lib/api";

const DEFAULT_CANDIDATES = [
  { id: "opt_tests_errors", title: "Add tests + error handling (repo standard)" },
  {
    id: "opt_enterprise",
    title: "Enterprise hardening (observability, SLOs, etc.)",
  },
];

export default function PlaygroundPage() {
  const [scopes, setScopes] = useState(["repo:continuum-demo"]);
  const [prompt, setPrompt] = useState("Make it production-ready");
  const [loading, setLoading] = useState(false);

  const [binding, setBinding] = useState<DecisionRecord[]>([]);
  const [lastResolution, setLastResolution] = useState<ResolveResult | null>(null);
  const [lastEnforcement, setLastEnforcement] = useState<EnforcementResult | null>(null);
  const [selectedDecision, setSelectedDecision] = useState<DecisionRecord | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const primaryScope = scopes[0] || "";

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

  // ---- Actions ----

  const sendPrompt = async () => {
    const p = prompt.trim();
    if (!p) return;
    setLoading(true);
    setLastEnforcement(null);
    setStatusMessage(null);
    try {
      const candidates = p.toLowerCase().includes("production-ready")
        ? DEFAULT_CANDIDATES
        : undefined;
      const data = await fetchResolve(p, primaryScope, candidates);
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

  const handleResolveOnly = sendPrompt;

  const handleEnforce = async () => {
    setLoading(true);
    setStatusMessage(null);
    try {
      const data = await fetchEnforce(primaryScope, {
        type: "code_change",
        description: prompt.trim() || "Do a full rewrite of auth module",
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

  const promoteInterpretation = async (
    selectedId: string,
    selectedTitle: string,
    scope: string
  ) => {
    setLoading(true);
    try {
      await fetchCommit({
        title: "production-ready",
        scope,
        decision_type: "interpretation",
        rationale: `In this repo, production-ready means: ${selectedTitle}.`,
        metadata: { selected_option_id: selectedId },
        activate: true,
      });
      setLastResolution(null);
      setStatusMessage(`Promoted to decision: production-ready -> ${selectedTitle}`);
      await refreshInspector();
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

        {/* Input bar */}
        <div className="mt-4">
          <input
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) void sendPrompt();
            }}
            placeholder="Ask anything..."
            className="w-full rounded-lg border border-zinc-200 bg-white px-4 py-2.5 text-sm shadow-sm outline-none focus:ring-2 focus:ring-teal-500/30 dark:border-zinc-800 dark:bg-zinc-950"
          />
        </div>

        {/* Action buttons */}
        <div className="mt-3 flex gap-2">
          <button
            onClick={sendPrompt}
            disabled={loading}
            className="rounded-lg bg-teal-600 px-5 py-2 text-sm font-medium text-white hover:bg-teal-700 disabled:opacity-50"
          >
            Send
          </button>
          <button
            onClick={handleResolveOnly}
            disabled={loading}
            className="rounded-lg border border-zinc-200 bg-white px-4 py-2 text-sm font-medium hover:bg-zinc-50 disabled:opacity-50 dark:border-zinc-800 dark:bg-zinc-950 dark:hover:bg-zinc-900"
          >
            Resolve Only
          </button>
          <button
            onClick={handleEnforce}
            disabled={loading}
            className="rounded-lg border border-zinc-200 bg-white px-4 py-2 text-sm font-medium hover:bg-zinc-50 disabled:opacity-50 dark:border-zinc-800 dark:bg-zinc-950 dark:hover:bg-zinc-900"
          >
            Enforce
          </button>
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
            />
          </div>
        )}
      </div>

      {/* Inspector panel */}
      <InspectorPanel
        decisions={binding}
        scopes={scopes}
        onSelectDecision={setSelectedDecision}
      />
    </div>
  );
}
