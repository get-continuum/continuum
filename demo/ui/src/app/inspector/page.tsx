"use client";

import { useCallback, useEffect, useState } from "react";
import ScopePills from "@/components/ScopePills";
import DecisionArtifact from "@/components/DecisionArtifact";
import ConflictDrawer from "@/components/ConflictDrawer";
import { fetchInspect } from "@/lib/api";
import type { DecisionRecord, ConflictNote } from "@/lib/api";

export default function InspectorPage() {
  const [scopes, setScopes] = useState(["repo:continuum-demo"]);
  const [binding, setBinding] = useState<DecisionRecord[]>([]);
  const [conflictNotes, setConflictNotes] = useState<ConflictNote[]>([]);
  const [selected, setSelected] = useState<DecisionRecord | null>(null);
  const [loading, setLoading] = useState(false);
  const [showConflicts, setShowConflicts] = useState(true);

  const primaryScope = scopes[0] || "";

  const refresh = useCallback(async () => {
    if (!primaryScope) return;
    setLoading(true);
    try {
      const data = await fetchInspect(primaryScope);
      setBinding(data.binding ?? []);
      setConflictNotes(data.conflict_notes ?? []);
      setShowConflicts(true);
    } catch {
      setBinding([]);
      setConflictNotes([]);
    } finally {
      setLoading(false);
    }
  }, [primaryScope]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return (
    <div className="animate-fadeIn p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-white">Inspector</h1>
        <button
          onClick={refresh}
          disabled={loading}
          className="text-xs text-zinc-500 transition-colors hover:text-zinc-300 disabled:opacity-50"
        >
          Refresh
        </button>
      </div>

      <div className="mt-4">
        <ScopePills scopes={scopes} onChange={setScopes} />
      </div>

      <p className="mt-4 text-xs text-zinc-500">
        Active binding set for <code className="text-zinc-400">{primaryScope}</code> &mdash;{" "}
        <span className="font-medium text-zinc-300">
          {binding.length} decision{binding.length !== 1 ? "s" : ""}
        </span>
      </p>

      {/* Conflict banner */}
      {showConflicts && conflictNotes.length > 0 && (
        <div className="mt-4">
          <ConflictDrawer
            conflictNotes={conflictNotes}
            decisions={binding}
            onClose={() => setShowConflicts(false)}
          />
        </div>
      )}

      <div className="mt-4 grid grid-cols-1 gap-3 lg:grid-cols-2">
        {binding.length === 0 && !loading && (
          <div className="rounded-lg border border-white/[0.06] bg-white/[0.03] p-4 text-sm text-zinc-500">
            No active decisions for this scope.
          </div>
        )}
        {binding.map((d) => (
          <button
            key={d.id}
            onClick={() => setSelected(d)}
            className={[
              "w-full rounded-xl border p-4 text-left text-sm transition-all",
              selected?.id === d.id
                ? "border-teal-500/30 bg-teal-500/5"
                : "border-white/[0.08] bg-[#111115] hover:border-white/15",
            ].join(" ")}
          >
            <div className="flex items-start justify-between gap-2">
              <span className="font-medium text-zinc-200">{d.title}</span>
              <span
                className={[
                  "shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium",
                  d.status === "active"
                    ? "bg-emerald-500/15 text-emerald-400"
                    : "bg-zinc-500/15 text-zinc-400",
                ].join(" ")}
              >
                {d.status}
              </span>
            </div>
            <div className="mt-1 text-[11px] text-zinc-500">
              <code>{d.id}</code>
              {d.enforcement?.decision_type && (
                <span className="ml-2 rounded bg-white/5 px-1.5 py-0.5">
                  {d.enforcement.decision_type}
                </span>
              )}
            </div>
          </button>
        ))}
      </div>

      {selected && (
        <div className="mt-6">
          <DecisionArtifact
            decision={selected}
            onClose={() => setSelected(null)}
          />
        </div>
      )}
    </div>
  );
}
