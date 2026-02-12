"use client";

import { useCallback, useEffect, useState } from "react";
import ScopePills from "@/components/ScopePills";
import DecisionGraph from "@/components/DecisionGraph";
import DecisionArtifact from "@/components/DecisionArtifact";
import { fetchGraph } from "@/lib/api";
import type { GraphNode, GraphEdge, DecisionRecord } from "@/lib/api";
import { getJson } from "@/lib/api";

export default function GraphPage() {
  const [scopes, setScopes] = useState(["repo:continuum-demo"]);
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedDecision, setSelectedDecision] = useState<DecisionRecord | null>(null);
  const [loading, setLoading] = useState(false);

  const primaryScope = scopes[0] || "";

  const refresh = useCallback(async () => {
    if (!primaryScope) return;
    setLoading(true);
    try {
      const data = await fetchGraph(primaryScope);
      setNodes(data.nodes ?? []);
      setEdges(data.edges ?? []);
    } catch {
      setNodes([]);
      setEdges([]);
    } finally {
      setLoading(false);
    }
  }, [primaryScope]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const handleSelectNode = async (nodeId: string) => {
    setSelectedNodeId(nodeId);
    // If it's a decision node, fetch its details
    if (!nodeId.startsWith("scope:")) {
      try {
        const data = await getJson<{ decision: DecisionRecord }>(
          `/decision/${encodeURIComponent(nodeId)}`
        );
        setSelectedDecision(data.decision);
      } catch {
        setSelectedDecision(null);
      }
    } else {
      setSelectedDecision(null);
    }
  };

  return (
    <div className="animate-fadeIn p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-white">Graph</h1>
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
        Decision lineage and scope graph for{" "}
        <code className="text-zinc-400">{primaryScope}</code> &mdash;{" "}
        <span className="font-medium text-zinc-300">
          {nodes.filter((n) => n.type === "decision").length} decisions,{" "}
          {nodes.filter((n) => n.type === "scope").length} scopes
        </span>
      </p>

      <div className="mt-4">
        <DecisionGraph
          nodes={nodes}
          edges={edges}
          onSelectNode={handleSelectNode}
          selectedNodeId={selectedNodeId}
        />
      </div>

      {selectedDecision && (
        <div className="mt-6">
          <DecisionArtifact
            decision={selectedDecision}
            onClose={() => {
              setSelectedDecision(null);
              setSelectedNodeId(null);
            }}
          />
        </div>
      )}
    </div>
  );
}
