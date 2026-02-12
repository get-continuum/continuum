"use client";

import { useMemo } from "react";
import type { GraphNode, GraphEdge } from "@/lib/api";

type Props = {
  nodes: GraphNode[];
  edges: GraphEdge[];
  onSelectNode: (nodeId: string) => void;
  selectedNodeId: string | null;
};

const STATUS_COLORS: Record<string, string> = {
  active: "border-emerald-500/40 bg-emerald-500/10",
  superseded: "border-amber-500/40 bg-amber-500/10",
  archived: "border-red-500/40 bg-red-500/10",
  draft: "border-zinc-500/40 bg-zinc-500/10",
};

const EDGE_TYPE_LABELS: Record<string, string> = {
  applies_to: "applies to",
  supersedes: "supersedes",
  overrides: "overrides",
};

export default function DecisionGraph({
  nodes,
  edges,
  onSelectNode,
  selectedNodeId,
}: Props) {
  const decisionNodes = useMemo(
    () => nodes.filter((n) => n.type === "decision"),
    [nodes]
  );
  const scopeNodes = useMemo(
    () => nodes.filter((n) => n.type === "scope"),
    [nodes]
  );

  const supersedeEdges = useMemo(
    () => edges.filter((e) => e.type === "supersedes"),
    [edges]
  );

  if (nodes.length === 0) {
    return (
      <div className="rounded-lg border border-white/[0.06] bg-white/[0.03] p-8 text-center text-sm text-zinc-500">
        No decisions to display. Commit some decisions first.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Scope groups */}
      {scopeNodes.map((scopeNode) => {
        const scopeId = scopeNode.id;
        const scopeName = String(scopeNode.data.scope || scopeId);
        const connectedDecisionIds = edges
          .filter((e) => e.target === scopeId && e.type === "applies_to")
          .map((e) => e.source);
        const scopeDecisions = decisionNodes.filter((d) =>
          connectedDecisionIds.includes(d.id)
        );

        return (
          <div key={scopeId} className="rounded-xl border border-white/[0.08] bg-[#111115] p-4">
            <div className="flex items-center gap-2 mb-3">
              <span className="rounded-full bg-blue-500/15 px-2.5 py-0.5 text-[10px] font-bold uppercase text-blue-400">
                Scope
              </span>
              <code className="text-sm text-zinc-300">{scopeName}</code>
              <span className="text-[10px] text-zinc-500">
                ({scopeDecisions.length} decision{scopeDecisions.length !== 1 ? "s" : ""})
              </span>
            </div>

            <div className="grid grid-cols-1 gap-2 md:grid-cols-2 lg:grid-cols-3">
              {scopeDecisions.map((node) => {
                const data = node.data;
                const status = String(data.status || "draft");
                const isSelected = selectedNodeId === node.id;

                // Check if this decision supersedes another
                const supersedeTarget = supersedeEdges.find(
                  (e) => e.source === node.id
                );

                return (
                  <button
                    key={node.id}
                    onClick={() => onSelectNode(node.id)}
                    className={[
                      "w-full rounded-lg border p-3 text-left text-sm transition-all",
                      isSelected
                        ? "border-teal-500/40 bg-teal-500/10 ring-1 ring-teal-500/20"
                        : STATUS_COLORS[status] || STATUS_COLORS.draft,
                      "hover:brightness-110",
                    ].join(" ")}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span className="font-medium text-zinc-200 text-xs">
                        {String(data.title || node.id)}
                      </span>
                      <span
                        className={[
                          "shrink-0 rounded-full px-1.5 py-0.5 text-[9px] font-medium",
                          status === "active"
                            ? "bg-emerald-500/20 text-emerald-400"
                            : status === "superseded"
                            ? "bg-amber-500/20 text-amber-400"
                            : "bg-zinc-500/20 text-zinc-400",
                        ].join(" ")}
                      >
                        {status}
                      </span>
                    </div>
                    <div className="mt-1 flex items-center gap-2">
                      <code className="text-[10px] text-zinc-600">{node.id}</code>
                      {data.decision_type && (
                        <span className="rounded bg-white/5 px-1 py-0.5 text-[9px] text-zinc-500">
                          {String(data.decision_type)}
                        </span>
                      )}
                    </div>
                    {supersedeTarget && (
                      <div className="mt-1.5 flex items-center gap-1 text-[10px] text-amber-400/70">
                        <span>&#8599;</span>
                        <span>
                          {EDGE_TYPE_LABELS.supersedes}{" "}
                          <code>{supersedeTarget.target}</code>
                        </span>
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        );
      })}

      {/* Orphan decisions (no scope edge) */}
      {(() => {
        const connectedIds = new Set(
          edges.filter((e) => e.type === "applies_to").map((e) => e.source)
        );
        const orphans = decisionNodes.filter((d) => !connectedIds.has(d.id));
        if (orphans.length === 0) return null;

        return (
          <div className="rounded-xl border border-white/[0.08] bg-[#111115] p-4">
            <div className="flex items-center gap-2 mb-3">
              <span className="rounded-full bg-zinc-500/15 px-2.5 py-0.5 text-[10px] font-bold uppercase text-zinc-400">
                Unscoped
              </span>
            </div>
            <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
              {orphans.map((node) => (
                <button
                  key={node.id}
                  onClick={() => onSelectNode(node.id)}
                  className="w-full rounded-lg border border-zinc-500/20 bg-zinc-500/5 p-3 text-left text-xs text-zinc-400 transition-all hover:brightness-110"
                >
                  {String(node.data.title || node.id)}
                </button>
              ))}
            </div>
          </div>
        );
      })()}
    </div>
  );
}
