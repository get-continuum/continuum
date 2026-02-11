"use client";

import { useCallback, useEffect, useState } from "react";
import ScopePills from "@/components/ScopePills";
import DecisionArtifact from "@/components/DecisionArtifact";
import { fetchInspect } from "@/lib/api";
import type { DecisionRecord } from "@/lib/api";

export default function InspectorPage() {
  const [scopes, setScopes] = useState(["repo:continuum-demo"]);
  const [binding, setBinding] = useState<DecisionRecord[]>([]);
  const [selected, setSelected] = useState<DecisionRecord | null>(null);
  const [loading, setLoading] = useState(false);

  const primaryScope = scopes[0] || "";

  const refresh = useCallback(async () => {
    if (!primaryScope) return;
    setLoading(true);
    try {
      const data = await fetchInspect(primaryScope);
      setBinding(data.binding ?? []);
    } catch {
      setBinding([]);
    } finally {
      setLoading(false);
    }
  }, [primaryScope]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return (
    <div className="p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold">Inspector</h1>
        <button
          onClick={refresh}
          disabled={loading}
          className="text-xs text-zinc-500 hover:text-zinc-900 disabled:opacity-50 dark:hover:text-zinc-50"
        >
          Refresh
        </button>
      </div>

      <div className="mt-4">
        <ScopePills scopes={scopes} onChange={setScopes} />
      </div>

      <p className="mt-4 text-xs text-zinc-500 dark:text-zinc-400">
        Active binding set for <code>{primaryScope}</code> &mdash;{" "}
        <span className="font-medium">
          {binding.length} decision{binding.length !== 1 ? "s" : ""}
        </span>
      </p>

      <div className="mt-4 grid grid-cols-1 gap-3 lg:grid-cols-2">
        {binding.length === 0 && !loading && (
          <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-4 text-sm text-zinc-500 dark:border-zinc-800 dark:bg-zinc-900">
            No active decisions for this scope.
          </div>
        )}
        {binding.map((d) => (
          <button
            key={d.id}
            onClick={() => setSelected(d)}
            className={[
              "w-full rounded-xl border p-4 text-left text-sm transition-colors",
              selected?.id === d.id
                ? "border-teal-500 bg-teal-50 dark:border-teal-700 dark:bg-teal-950/30"
                : "border-zinc-200 bg-white hover:border-zinc-300 dark:border-zinc-800 dark:bg-zinc-950 dark:hover:border-zinc-700",
            ].join(" ")}
          >
            <div className="flex items-start justify-between gap-2">
              <span className="font-medium">{d.title}</span>
              <span
                className={[
                  "shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium",
                  d.status === "active"
                    ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400"
                    : "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400",
                ].join(" ")}
              >
                {d.status}
              </span>
            </div>
            <div className="mt-1 text-[11px] text-zinc-500">
              <code>{d.id}</code>
              {d.enforcement?.decision_type && (
                <span className="ml-2 rounded bg-zinc-200 px-1.5 py-0.5 dark:bg-zinc-800">
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
