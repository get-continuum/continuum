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

const inputClasses =
  "mt-1 w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder-zinc-500 outline-none transition-colors focus:border-teal-500/40 focus:ring-2 focus:ring-teal-500/20";

export default function PlaygroundPage() {
  const [scopes, setScopes] = useState(["repo:continuum-demo"]);
  const primaryScope = scopes[0] || "";

  const [title, setTitle] = useState("");
  const [formScope, setFormScope] = useState(primaryScope);
  const [decisionType, setDecisionType] = useState("interpretation");
  const [rationale, setRationale] = useState("");

  const [resolvePrompt, setResolvePrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [binding, setBinding] = useState<DecisionRecord[]>([]);
  const [lastResolution, setLastResolution] = useState<ResolveResult | null>(null);
  const [lastEnforcement, setLastEnforcement] = useState<EnforcementResult | null>(null);
  const [selectedDecision, setSelectedDecision] = useState<DecisionRecord | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  useEffect(() => {
    setFormScope(primaryScope);
  }, [primaryScope]);

  const refreshInspector = useCallback(async () => {
    if (!primaryScope) return;
    try {
      const data = await fetchInspect(primaryScope);
      setBinding(data.binding ?? []);
    } catch { /* ignore */ }
  }, [primaryScope]);

  useEffect(() => {
    void refreshInspector();
  }, [refreshInspector]);

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
          `Resolved by prior decision: ${(data.resolution as { matched_decision_id?: string }).matched_decision_id ?? "unknown"}`
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
      setStatusMessage(`Enforcement verdict: ${data.enforcement.verdict} (${data.enforcement.reason})`);
    } catch (e: unknown) {
      setStatusMessage(`Error: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setLoading(false);
      await refreshInspector();
    }
  };

  const promoteInterpretation = async (selectedId: string, selectedTitle: string, scope: string) => {
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

  const handleSupersede = (decision: DecisionRecord) => {
    const enforcement = decision.enforcement;
    setTitle(`${decision.title} (v2)`);
    setFormScope(enforcement?.scope || primaryScope);
    setDecisionType(enforcement?.decision_type || "interpretation");
    setRationale(`Supersedes: ${decision.id} — ${decision.title}`);
    setSelectedDecision(null);
    setStatusMessage(`Pre-filled form to supersede "${decision.title}". Edit and commit.`);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

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
      <div className="animate-fadeIn flex-1 overflow-auto p-6">
        <h1 className="text-lg font-semibold text-white">Playground</h1>

        <div className="mt-4">
          <ScopePills scopes={scopes} onChange={setScopes} />
        </div>

        {/* Commit Form */}
        <div className="mt-6 rounded-xl border border-white/[0.08] bg-[#111115] p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-zinc-200">
            Commit a Decision
          </h2>
          <div className="mt-3 grid grid-cols-2 gap-3">
            <div className="col-span-2">
              <label className="text-xs font-medium text-zinc-500">Title</label>
              <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Use bullet-point responses" className={inputClasses} />
            </div>
            <div>
              <label className="text-xs font-medium text-zinc-500">Scope</label>
              <input value={formScope} onChange={(e) => setFormScope(e.target.value)} placeholder="e.g. repo:my-app" className={inputClasses} />
            </div>
            <div>
              <label className="text-xs font-medium text-zinc-500">Type</label>
              <select value={decisionType} onChange={(e) => setDecisionType(e.target.value)} className={inputClasses}>
                {DECISION_TYPES.map((t) => (<option key={t} value={t}>{t}</option>))}
              </select>
            </div>
            <div className="col-span-2">
              <label className="text-xs font-medium text-zinc-500">
                Rationale <span className="text-zinc-600">(optional)</span>
              </label>
              <textarea value={rationale} onChange={(e) => setRationale(e.target.value)} rows={2} placeholder="Why was this decided?" className={inputClasses + " resize-none"} />
            </div>
          </div>
          <button onClick={handleCommit} disabled={loading || !title.trim()} className="mt-3 rounded-lg bg-teal-600 px-5 py-2 text-sm font-medium text-white transition-all hover:bg-teal-500 hover:shadow-lg hover:shadow-teal-600/20 disabled:opacity-50">
            Commit Decision
          </button>
        </div>

        {/* Resolve / Enforce */}
        <div className="mt-6 rounded-xl border border-white/[0.08] bg-[#111115] p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-zinc-200">
            Resolve &amp; Enforce
          </h2>
          <p className="mt-1 text-xs text-zinc-500">
            Test how your decisions respond to queries and actions.
          </p>
          <div className="mt-3">
            <input
              value={resolvePrompt}
              onChange={(e) => setResolvePrompt(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) void handleResolve(); }}
              placeholder="Ask anything... e.g. Make it production-ready"
              className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-zinc-500 outline-none transition-colors focus:border-teal-500/40 focus:ring-2 focus:ring-teal-500/20"
            />
          </div>
          <div className="mt-3 flex gap-2">
            <button onClick={handleResolve} disabled={loading || !resolvePrompt.trim()} className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-500 disabled:opacity-50">
              Resolve
            </button>
            <button onClick={handleEnforce} disabled={loading} className="rounded-lg border border-white/10 px-4 py-2 text-sm font-medium text-zinc-300 transition-colors hover:bg-white/5 disabled:opacity-50">
              Enforce
            </button>
          </div>
        </div>

        {/* Status */}
        {statusMessage && (
          <div className="mt-4 rounded-lg border border-white/[0.06] bg-white/[0.03] p-3 text-sm text-zinc-300">
            {statusMessage}
          </div>
        )}

        {/* Ambiguity card */}
        {lastResolution && lastResolution.status === "needs_clarification" && (
          <div className="mt-4">
            <AmbiguityCard result={lastResolution} prompt={resolvePrompt} loading={loading} onCommit={promoteInterpretation} scopes={scopes} />
          </div>
        )}

        {/* Enforcement result */}
        {lastEnforcement && (
          <div
            className={[
              "mt-4 rounded-xl border p-4 text-sm",
              lastEnforcement.verdict === "block"
                ? "border-red-500/20 bg-red-500/5"
                : lastEnforcement.verdict === "confirm"
                ? "border-amber-500/20 bg-amber-500/5"
                : "border-emerald-500/20 bg-emerald-500/5",
            ].join(" ")}
          >
            <div className="text-xs font-semibold text-zinc-300">Enforcement Result</div>
            <div className="mt-1 flex items-center gap-2">
              <span
                className={[
                  "rounded-full px-2 py-0.5 text-[10px] font-bold uppercase",
                  lastEnforcement.verdict === "block"
                    ? "bg-red-500/15 text-red-400"
                    : lastEnforcement.verdict === "confirm"
                    ? "bg-amber-500/15 text-amber-400"
                    : "bg-emerald-500/15 text-emerald-400",
                ].join(" ")}
              >
                {lastEnforcement.verdict}
              </span>
              <span className="text-xs text-zinc-400">{lastEnforcement.reason}</span>
            </div>
          </div>
        )}

        {/* Decision Artifact */}
        {selectedDecision && (
          <div className="mt-4">
            <DecisionArtifact decision={selectedDecision} onClose={() => setSelectedDecision(null)} onSupersede={() => handleSupersede(selectedDecision)} onArchive={() => handleArchive(selectedDecision)} />
          </div>
        )}
      </div>

      <InspectorPanel decisions={binding} scopes={scopes} onSelectDecision={setSelectedDecision} onSupersede={handleSupersede} onArchive={handleArchive} />
    </div>
  );
}
