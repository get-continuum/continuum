"use client";

import type { DecisionRecord } from "@/lib/api";

type Props = {
  decision: DecisionRecord;
  onClose?: () => void;
};

export default function DecisionArtifact({ decision, onClose }: Props) {
  const enforcement = decision.enforcement;

  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-base">📋</span>
          <h3 className="text-sm font-semibold">Decision Artifact</h3>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-xs text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-50"
          >
            Close
          </button>
        )}
      </div>

      {/* Pills */}
      <div className="mt-3 flex flex-wrap gap-2">
        {enforcement?.decision_type && (
          <span className="rounded-full bg-teal-100 px-2.5 py-0.5 text-[11px] font-medium text-teal-800 dark:bg-teal-900/30 dark:text-teal-300">
            Type: {enforcement.decision_type}
          </span>
        )}
        {enforcement?.scope && (
          <span className="rounded-full bg-blue-100 px-2.5 py-0.5 text-[11px] font-medium text-blue-800 dark:bg-blue-900/30 dark:text-blue-300">
            Scope: {enforcement.scope}
          </span>
        )}
        <span className="rounded-full bg-zinc-100 px-2.5 py-0.5 text-[11px] font-medium text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">
          Version: {decision.version ?? 0}
        </span>
      </div>

      {/* Rationale */}
      {decision.rationale && (
        <div className="mt-3">
          <div className="text-[11px] font-medium text-zinc-500 dark:text-zinc-400">
            Rationale
          </div>
          <p className="mt-1 rounded-lg border border-zinc-100 bg-zinc-50 p-2.5 text-sm text-zinc-800 dark:border-zinc-900 dark:bg-black dark:text-zinc-200">
            {decision.rationale}
          </p>
        </div>
      )}

      {/* Metadata / Binding */}
      {decision.metadata && Object.keys(decision.metadata).length > 0 && (
        <div className="mt-3">
          <div className="text-[11px] font-medium text-zinc-500 dark:text-zinc-400">
            Binding
          </div>
          <pre className="mt-1 overflow-auto rounded-lg border border-zinc-100 bg-zinc-50 p-2.5 text-xs text-zinc-700 dark:border-zinc-900 dark:bg-black dark:text-zinc-300">
            {JSON.stringify(decision.metadata, null, 2)}
          </pre>
        </div>
      )}

      {/* Options */}
      {decision.options_considered && decision.options_considered.length > 0 && (
        <div className="mt-3">
          <div className="text-[11px] font-medium text-zinc-500 dark:text-zinc-400">
            Options Considered
          </div>
          <div className="mt-1 space-y-1">
            {decision.options_considered.map((opt) => (
              <div
                key={opt.id}
                className={[
                  "flex items-center gap-2 rounded-md border px-2 py-1.5 text-xs",
                  opt.selected
                    ? "border-emerald-200 bg-emerald-50 dark:border-emerald-900/40 dark:bg-emerald-950/30"
                    : "border-zinc-100 bg-zinc-50 dark:border-zinc-900 dark:bg-black",
                ].join(" ")}
              >
                <span
                  className={
                    opt.selected
                      ? "text-emerald-600 dark:text-emerald-400"
                      : "text-zinc-400"
                  }
                >
                  {opt.selected ? "+" : "-"}
                </span>
                <span className={opt.selected ? "font-medium" : "line-through opacity-60"}>
                  {opt.title}
                </span>
                {opt.rejected_reason && (
                  <span className="ml-auto text-[10px] text-zinc-500">
                    ({opt.rejected_reason})
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Supersedes */}
      {enforcement?.supersedes && (
        <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 p-2 text-xs dark:border-amber-900/40 dark:bg-amber-950/30">
          <span className="font-medium text-amber-800 dark:text-amber-300">
            Supersedes:
          </span>{" "}
          <code className="text-amber-900 dark:text-amber-200">
            {enforcement.supersedes}
          </code>
        </div>
      )}

      {/* Timestamps */}
      {decision.created_at && (
        <div className="mt-3 text-[10px] text-zinc-400">
          Created: {new Date(decision.created_at).toLocaleString()}
          {decision.updated_at && decision.updated_at !== decision.created_at && (
            <>
              {" "}
              | Updated: {new Date(decision.updated_at).toLocaleString()}
            </>
          )}
        </div>
      )}
    </div>
  );
}
