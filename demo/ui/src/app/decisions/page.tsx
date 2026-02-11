"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import HierarchyExplorer from "@/components/HierarchyExplorer";
import ActionMenu from "@/components/ActionMenu";
import {
  fetchDecisions,
  patchDecisionStatus,
  fetchSupersede,
} from "@/lib/api";
import type { DecisionRecord } from "@/lib/api";
import { timeAgo, cn } from "@/lib/utils";

/* ------------------------------------------------------------------ */
/*  Constants                                                          */
/* ------------------------------------------------------------------ */

const CATEGORY_COLORS: Record<string, string> = {
  interpretation: "bg-teal-500",
  preference: "bg-blue-500",
  behavior_rule: "bg-purple-500",
  rejection: "bg-red-500",
  standard: "bg-amber-500",
  guideline: "bg-emerald-500",
  constraint: "bg-rose-500",
};

const DATE_RANGES = [
  { label: "All Time", days: 0 },
  { label: "1d", days: 1 },
  { label: "7d", days: 7 },
  { label: "30d", days: 30 },
] as const;

/* ------------------------------------------------------------------ */
/*  Skeleton row                                                       */
/* ------------------------------------------------------------------ */

function SkeletonRow() {
  return (
    <tr>
      <td className="px-4 py-3"><div className="skeleton h-3 w-28" /></td>
      <td className="px-4 py-3"><div className="skeleton h-4 w-20 rounded-full" /></td>
      <td className="px-4 py-3"><div className="skeleton h-3 w-48" /></td>
      <td className="px-4 py-3"><div className="skeleton h-4 w-16 rounded-full" /></td>
      <td className="px-4 py-3"><div className="skeleton h-3 w-4" /></td>
    </tr>
  );
}

/* ------------------------------------------------------------------ */
/*  Main component                                                     */
/* ------------------------------------------------------------------ */

export default function DecisionsPage() {
  const [decisions, setDecisions] = useState<DecisionRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [scopeFilter, setScopeFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [dateRange, setDateRange] = useState(0);
  const [selected, setSelected] = useState<DecisionRecord | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const scope = scopeFilter.trim() || undefined;
      const data = await fetchDecisions(scope);
      setDecisions(data.decisions ?? []);
    } catch {
      setDecisions([]);
    } finally {
      setLoading(false);
    }
  }, [scopeFilter]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const categories = useMemo(() => {
    const set = new Set<string>();
    for (const d of decisions) {
      if (d.enforcement?.decision_type) set.add(d.enforcement.decision_type);
    }
    return Array.from(set).sort();
  }, [decisions]);

  const filtered = useMemo(() => {
    let list = decisions;
    if (categoryFilter !== "all") {
      list = list.filter((d) => d.enforcement?.decision_type === categoryFilter);
    }
    if (dateRange > 0) {
      const cutoff = Date.now() - dateRange * 24 * 60 * 60 * 1000;
      list = list.filter((d) => d.created_at && new Date(d.created_at).getTime() >= cutoff);
    }
    return list;
  }, [decisions, categoryFilter, dateRange]);

  const handleArchive = async (d: DecisionRecord) => {
    setActionLoading(d.id);
    setStatusMessage(null);
    try {
      await patchDecisionStatus(d.id, "archived");
      setStatusMessage(`Archived: ${d.title}`);
      setSelected(null);
      await refresh();
    } catch (e: unknown) {
      setStatusMessage(`Failed: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleSupersede = async (d: DecisionRecord) => {
    const newTitle = prompt(`New title to supersede "${d.title}":`);
    if (!newTitle) return;
    setActionLoading(d.id);
    setStatusMessage(null);
    try {
      await fetchSupersede({ old_id: d.id, new_title: newTitle, rationale: `Supersedes: ${d.title}` });
      setStatusMessage(`Superseded "${d.title}" with "${newTitle}"`);
      setSelected(null);
      await refresh();
    } catch (e: unknown) {
      setStatusMessage(`Failed: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="animate-fadeIn p-6">
      {/* Header row */}
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-white">Decisions</h1>
        <div className="flex items-center gap-2">
          {/* Date range */}
          <div className="flex items-center overflow-hidden rounded-lg border border-white/10">
            {DATE_RANGES.map((r) => (
              <button
                key={r.label}
                onClick={() => setDateRange(r.days)}
                className={cn(
                  "px-3 py-1.5 text-xs font-medium transition-colors",
                  dateRange === r.days
                    ? "bg-white/10 text-white"
                    : "text-zinc-500 hover:bg-white/5 hover:text-zinc-300"
                )}
              >
                {r.label}
              </button>
            ))}
          </div>

          <button
            onClick={() => setShowFilters(!showFilters)}
            className={cn(
              "flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors",
              showFilters
                ? "border-teal-500/30 bg-teal-500/10 text-teal-400"
                : "border-white/10 text-zinc-400 hover:bg-white/5"
            )}
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M2 3.5H12M4 7H10M6 10.5H8" stroke="currentColor" strokeWidth="1.25" strokeLinecap="round" />
            </svg>
            Filters
          </button>

          <button
            onClick={refresh}
            disabled={loading}
            className="flex items-center gap-1.5 rounded-lg border border-white/10 px-3 py-1.5 text-xs font-medium text-zinc-400 transition-colors hover:bg-white/5 disabled:opacity-50"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" className={cn(loading && "animate-spin")}>
              <path d="M11.5 7A4.5 4.5 0 1 1 7 2.5M7 2.5V5.5M7 2.5L9.5 2.5" stroke="currentColor" strokeWidth="1.25" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            Refresh
          </button>
        </div>
      </div>

      {/* Category pills */}
      <div className="mt-4 flex flex-wrap gap-2">
        <button
          onClick={() => setCategoryFilter("all")}
          className={cn(
            "flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition-colors",
            categoryFilter === "all"
              ? "border-white/20 bg-white/10 text-white"
              : "border-white/10 text-zinc-500 hover:text-zinc-300"
          )}
        >
          <span className="inline-block h-2 w-2 rounded-full bg-zinc-500" />
          Overview
        </button>
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setCategoryFilter(categoryFilter === cat ? "all" : cat)}
            className={cn(
              "flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition-colors",
              categoryFilter === cat
                ? "border-white/20 bg-white/10 text-white"
                : "border-white/10 text-zinc-500 hover:text-zinc-300"
            )}
          >
            <span className={cn("inline-block h-2 w-2 rounded-full", CATEGORY_COLORS[cat] || "bg-zinc-500")} />
            {cat.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
          </button>
        ))}
      </div>

      {/* Filters panel */}
      {showFilters && (
        <div className="mt-3 flex gap-3 rounded-lg border border-white/[0.06] bg-white/[0.03] p-3">
          <input
            value={scopeFilter}
            onChange={(e) => setScopeFilter(e.target.value)}
            placeholder="Filter by scope..."
            className="rounded-md border border-white/10 bg-white/5 px-3 py-1.5 text-sm text-white placeholder-zinc-500 outline-none focus:border-blue-500/40 focus:ring-2 focus:ring-blue-500/20"
          />
        </div>
      )}

      {/* Status message */}
      {statusMessage && (
        <div className="mt-3 rounded-lg border border-white/[0.06] bg-white/[0.03] p-2.5 text-sm text-zinc-300">
          {statusMessage}
        </div>
      )}

      {/* Table */}
      <div className="mt-4 overflow-hidden rounded-xl border border-white/[0.08]">
        <table className="w-full text-sm">
          <thead className="bg-white/[0.03] text-left text-xs text-zinc-500">
            <tr>
              <th className="px-4 py-2.5 font-medium">
                <div className="flex items-center gap-1">
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" className="text-zinc-600">
                    <circle cx="6" cy="6" r="5" stroke="currentColor" strokeWidth="1" />
                    <path d="M6 3V6L8 7.5" stroke="currentColor" strokeWidth="1" strokeLinecap="round" />
                  </svg>
                  Created At
                </div>
              </th>
              <th className="px-4 py-2.5 font-medium">
                <div className="flex items-center gap-1">
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" className="text-zinc-600">
                    <rect x="1" y="3" width="10" height="7" rx="1.5" stroke="currentColor" strokeWidth="1" />
                    <path d="M4 1V4M8 1V4" stroke="currentColor" strokeWidth="1" strokeLinecap="round" />
                  </svg>
                  Entities
                </div>
              </th>
              <th className="px-4 py-2.5 font-medium">
                <div className="flex items-center gap-1">
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" className="text-zinc-600">
                    <path d="M2 3H10M2 6H8M2 9H6" stroke="currentColor" strokeWidth="1" strokeLinecap="round" />
                  </svg>
                  Decision Content
                </div>
              </th>
              <th className="px-4 py-2.5 font-medium">
                <div className="flex items-center gap-1">
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" className="text-zinc-600">
                    <circle cx="4" cy="6" r="2.5" stroke="currentColor" strokeWidth="1" />
                    <circle cx="8" cy="6" r="2.5" stroke="currentColor" strokeWidth="1" />
                  </svg>
                  Categories
                </div>
              </th>
              <th className="px-4 py-2.5 font-medium">
                <div className="flex items-center gap-1">
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" className="text-zinc-600">
                    <circle cx="6" cy="6" r="1" fill="currentColor" />
                    <circle cx="6" cy="2.5" r="1" fill="currentColor" />
                    <circle cx="6" cy="9.5" r="1" fill="currentColor" />
                  </svg>
                  Actions
                </div>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04]">
            {loading && (<><SkeletonRow /><SkeletonRow /><SkeletonRow /><SkeletonRow /></>)}

            {!loading && filtered.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-10 text-center text-zinc-500">
                  <div className="flex flex-col items-center gap-2">
                    <svg width="32" height="32" viewBox="0 0 32 32" fill="none" className="text-zinc-700">
                      <rect x="4" y="6" width="24" height="20" rx="3" stroke="currentColor" strokeWidth="1.5" />
                      <path d="M10 14H22M10 18H18" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                    </svg>
                    <span className="text-sm">No decisions found.</span>
                  </div>
                </td>
              </tr>
            )}

            {!loading && filtered.map((d) => {
              const scope = d.enforcement?.scope || "";
              const decisionType = d.enforcement?.decision_type || "";
              const statusClasses =
                d.status === "active" ? "bg-emerald-500/15 text-emerald-400"
                : d.status === "superseded" ? "bg-amber-500/15 text-amber-400"
                : d.status === "archived" ? "bg-red-500/15 text-red-400"
                : "bg-zinc-500/15 text-zinc-400";

              return (
                <tr
                  key={d.id}
                  onClick={() => setSelected(d)}
                  className={cn(
                    "cursor-pointer transition-colors hover:bg-white/[0.03]",
                    selected?.id === d.id && "bg-teal-500/5"
                  )}
                >
                  <td className="px-4 py-3 text-xs text-zinc-500">
                    {d.created_at ? timeAgo(d.created_at) : "—"}
                  </td>
                  <td className="px-4 py-3">
                    {scope && (
                      <span className="inline-flex items-center gap-1 rounded-md border border-white/10 bg-white/5 px-2 py-0.5 text-xs font-medium text-zinc-300">
                        <svg width="10" height="10" viewBox="0 0 10 10" fill="none" className="text-zinc-500">
                          <rect x="1" y="1" width="8" height="8" rx="1.5" stroke="currentColor" strokeWidth="1" />
                        </svg>
                        {scope}
                      </span>
                    )}
                  </td>
                  <td className="max-w-xs px-4 py-3">
                    <div className="font-medium text-zinc-200">{d.title}</div>
                    {d.rationale && (
                      <div className="mt-0.5 truncate text-xs text-zinc-500">
                        {d.rationale.length > 80 ? d.rationale.slice(0, 80) + "..." : d.rationale}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap items-center gap-1">
                      {decisionType && (
                        <span className="flex items-center gap-1 rounded-full border border-white/10 px-2 py-0.5 text-[10px] font-medium text-zinc-400">
                          <span className={cn("inline-block h-1.5 w-1.5 rounded-full", CATEGORY_COLORS[decisionType] || "bg-zinc-500")} />
                          {decisionType.replace(/_/g, " ")}
                        </span>
                      )}
                      <span className={cn("rounded-full px-2 py-0.5 text-[10px] font-medium", statusClasses)}>
                        {d.status}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <ActionMenu
                      items={[
                        { label: "View Detail", onClick: () => setSelected(d) },
                        ...(d.status === "active"
                          ? [
                              { label: "Supersede", onClick: () => handleSupersede(d) },
                              { label: "Archive", onClick: () => handleArchive(d), variant: "danger" as const },
                            ]
                          : []),
                      ]}
                    />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Detail panel */}
      {selected && (
        <div className="mt-4">
          <HierarchyExplorer
            decision={selected}
            onClose={() => setSelected(null)}
            onSupersede={() => handleSupersede(selected)}
            onArchive={() => handleArchive(selected)}
          />
        </div>
      )}
    </div>
  );
}
