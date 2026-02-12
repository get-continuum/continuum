"use client";

import { useState } from "react";
import type { DecisionCandidateRecord } from "@/lib/api";

type Props = {
  candidates: DecisionCandidateRecord[];
  onCommit: (candidate: DecisionCandidateRecord) => void;
  onDismiss: (candidateId: string) => void;
  onCommitAllSafe: () => void;
  loading: boolean;
};

const RISK_COLORS: Record<string, string> = {
  low: "bg-emerald-500/15 text-emerald-400",
  medium: "bg-amber-500/15 text-amber-400",
  high: "bg-red-500/15 text-red-400",
};

export default function DecisionInbox({
  candidates,
  onCommit,
  onDismiss,
  onCommitAllSafe,
  loading,
}: Props) {
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());

  if (candidates.length === 0) return null;

  const visible = candidates.filter((c) => !dismissed.has(c.id));
  const safeCount = visible.filter(
    (c) => c.risk === "low" && c.confidence >= 0.9
  ).length;

  const handleDismiss = (id: string) => {
    setDismissed((prev) => new Set(prev).add(id));
    onDismiss(id);
  };

  return (
    <div className="rounded-xl border border-white/[0.08] bg-[#111115] p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-zinc-200">
          Decision Inbox
          <span className="ml-2 text-xs font-normal text-zinc-500">
            ({visible.length} candidates)
          </span>
        </h2>
        {safeCount > 0 && (
          <button
            onClick={onCommitAllSafe}
            disabled={loading}
            className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-emerald-500 disabled:opacity-50"
          >
            Commit all safe ({safeCount})
          </button>
        )}
      </div>

      <div className="mt-3 space-y-2">
        {visible.map((candidate) => (
          <div
            key={candidate.id}
            className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-3"
          >
            <div className="flex items-center gap-2">
              <span
                className={[
                  "rounded-full px-2 py-0.5 text-[10px] font-bold uppercase",
                  RISK_COLORS[candidate.risk] || "bg-zinc-500/15 text-zinc-400",
                ].join(" ")}
              >
                {candidate.risk} risk
              </span>
              <span className="rounded-full bg-white/5 px-2 py-0.5 text-[10px] text-zinc-400">
                {candidate.decision_type}
              </span>
              <span className="text-[10px] text-zinc-500">
                {(candidate.confidence * 100).toFixed(0)}%
              </span>
            </div>

            <p className="mt-1.5 text-sm font-medium text-zinc-200">
              {candidate.title}
            </p>
            <p className="mt-0.5 text-xs text-zinc-500">{candidate.rationale}</p>

            {candidate.evidence.length > 0 && (
              <div className="mt-2 text-xs text-zinc-500 italic">
                &ldquo;{candidate.evidence[0].quote}&rdquo;
              </div>
            )}

            <div className="mt-3 flex items-center gap-2">
              <span className="text-[10px] text-zinc-600">
                Scope: {candidate.scope_suggestion}
              </span>
              <div className="ml-auto flex gap-2">
                <button
                  onClick={() => handleDismiss(candidate.id)}
                  disabled={loading}
                  className="rounded-lg border border-white/10 px-3 py-1 text-xs text-zinc-400 transition-colors hover:bg-white/5 disabled:opacity-50"
                >
                  Dismiss
                </button>
                <button
                  onClick={() => onCommit(candidate)}
                  disabled={loading}
                  className="rounded-lg bg-teal-600 px-3 py-1 text-xs font-medium text-white transition-colors hover:bg-teal-500 disabled:opacity-50"
                >
                  Commit
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
