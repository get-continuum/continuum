"use client";

import { useCallback, useEffect, useState } from "react";
import DecisionArtifact from "@/components/DecisionArtifact";
import { fetchDecisions, patchDecisionStatus, fetchSupersede } from "@/lib/api";
import type { DecisionRecord } from "@/lib/api";

export default function DecisionsPage() {
  const [decisions, setDecisions] = useState<DecisionRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [scopeFilter, setScopeFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [selected, setSelected] = useState<DecisionRecord | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

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

  const filtered =
    statusFilter === "all"
      ? decisions
      : decisions.filter((d) => d.status === statusFilter);

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
      await fetchSupersede({
        old_id: d.id,
        new_title: newTitle,
        rationale: `Supersedes: ${d.title}`,
      });
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
    <div className="p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold">Decisions</h1>
        <button
          onClick={refresh}
          disabled={loading}
          className="text-xs text-zinc-500 hover:text-zinc-900 disabled:opacity-50 dark:hover:text-zinc-50"
        >
          Refresh
        </button>
      </div>

      {/* Status message */}
      {statusMessage && (
        <div className="mt-3 rounded-lg border border-zinc-200 bg-zinc-50 p-2.5 text-sm text-zinc-700 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300">
          {statusMessage}
        </div>
      )}

      {/* Filters */}
      <div className="mt-4 flex gap-3">
        <input
          value={scopeFilter}
          onChange={(e) => setScopeFilter(e.target.value)}
          placeholder="Filter by scope..."
          className="rounded-md border border-zinc-200 px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-teal-500/30 dark:border-zinc-800 dark:bg-zinc-950"
        />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-md border border-zinc-200 px-3 py-1.5 text-sm dark:border-zinc-800 dark:bg-zinc-950"
        >
          <option value="all">All statuses</option>
          <option value="active">Active</option>
          <option value="draft">Draft</option>
          <option value="superseded">Superseded</option>
          <option value="archived">Archived</option>
        </select>
      </div>

      {/* Table */}
      <div className="mt-4 overflow-hidden rounded-xl border border-zinc-200 dark:border-zinc-800">
        <table className="w-full text-sm">
          <thead className="bg-zinc-50 text-left text-xs text-zinc-500 dark:bg-zinc-900 dark:text-zinc-400">
            <tr>
              <th className="px-4 py-2.5 font-medium">Title</th>
              <th className="px-4 py-2.5 font-medium">Type</th>
              <th className="px-4 py-2.5 font-medium">Scope</th>
              <th className="px-4 py-2.5 font-medium">Status</th>
              <th className="px-4 py-2.5 font-medium">Created</th>
              <th className="px-4 py-2.5 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
            {loading && (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-center text-zinc-400">
                  Loading...
                </td>
              </tr>
            )}
            {!loading && filtered.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-center text-zinc-400">
                  No decisions found.
                </td>
              </tr>
            )}
            {filtered.map((d) => (
              <tr
                key={d.id}
                className="cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-900"
              >
                <td
                  className="px-4 py-2.5 font-medium"
                  onClick={() => setSelected(d)}
                >
                  {d.title}
                </td>
                <td className="px-4 py-2.5" onClick={() => setSelected(d)}>
                  {d.enforcement?.decision_type && (
                    <span className="rounded-full bg-teal-100 px-2 py-0.5 text-[10px] font-medium text-teal-800 dark:bg-teal-900/30 dark:text-teal-300">
                      {d.enforcement.decision_type}
                    </span>
                  )}
                </td>
                <td className="px-4 py-2.5" onClick={() => setSelected(d)}>
                  <code className="text-xs">{d.enforcement?.scope}</code>
                </td>
                <td className="px-4 py-2.5" onClick={() => setSelected(d)}>
                  <span
                    className={[
                      "rounded-full px-2 py-0.5 text-[10px] font-medium",
                      d.status === "active"
                        ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400"
                        : d.status === "superseded"
                        ? "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400"
                        : d.status === "archived"
                        ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
                        : "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400",
                    ].join(" ")}
                  >
                    {d.status}
                  </span>
                </td>
                <td
                  className="px-4 py-2.5 text-zinc-500"
                  onClick={() => setSelected(d)}
                >
                  {d.created_at
                    ? new Date(d.created_at).toLocaleDateString()
                    : "—"}
                </td>
                <td className="px-4 py-2.5">
                  {d.status === "active" && (
                    <div className="flex gap-1">
                      <button
                        onClick={() => handleSupersede(d)}
                        disabled={actionLoading === d.id}
                        className="rounded bg-blue-50 px-2 py-0.5 text-[10px] font-medium text-blue-700 hover:bg-blue-100 disabled:opacity-50 dark:bg-blue-900/30 dark:text-blue-300"
                      >
                        Supersede
                      </button>
                      <button
                        onClick={() => handleArchive(d)}
                        disabled={actionLoading === d.id}
                        className="rounded bg-zinc-100 px-2 py-0.5 text-[10px] font-medium text-zinc-600 hover:bg-zinc-200 disabled:opacity-50 dark:bg-zinc-800 dark:text-zinc-400"
                      >
                        Archive
                      </button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Detail panel */}
      {selected && (
        <div className="mt-4">
          <DecisionArtifact
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
