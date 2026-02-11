"use client";

import type { DecisionRecord } from "@/lib/api";

type Props = {
  decisions: DecisionRecord[];
  scopes: string[];
  onSelectDecision?: (d: DecisionRecord) => void;
  onSupersede?: (d: DecisionRecord) => void;
  onArchive?: (d: DecisionRecord) => void;
};

const DOT_COLORS = [
  "bg-blue-500",
  "bg-emerald-500",
  "bg-purple-500",
  "bg-amber-500",
  "bg-rose-500",
];

export default function InspectorPanel({
  decisions,
  scopes,
  onSelectDecision,
  onSupersede,
  onArchive,
}: Props) {
  return (
    <aside className="flex w-72 shrink-0 flex-col border-l border-white/[0.06] bg-[#0a0a0f] p-4">
      {/* Applied Decisions */}
      <h3 className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
        Applied Decisions
      </h3>
      <div className="mt-2 space-y-1">
        {decisions.length === 0 && (
          <p className="text-xs text-zinc-600">No active decisions</p>
        )}
        {decisions.map((d, i) => {
          const dot = DOT_COLORS[i % DOT_COLORS.length];
          return (
            <div
              key={d.id}
              className="group rounded-md px-2 py-1.5 transition-colors hover:bg-white/5"
            >
              <button
                onClick={() => onSelectDecision?.(d)}
                className="flex w-full items-center gap-2 text-left text-xs"
              >
                <span className={`inline-block h-2 w-2 shrink-0 rounded-full ${dot}`} />
                <span className="truncate font-medium text-zinc-300">{d.title}</span>
              </button>
              <div className="mt-0.5 flex items-center gap-1 pl-4 text-[10px] text-zinc-500">
                <span>{d.enforcement?.decision_type}</span>
                <span className="mx-0.5">·</span>
                <code className="truncate">{d.enforcement?.scope}</code>
              </div>
              <div className="mt-1 flex gap-1 pl-4 opacity-0 transition-opacity group-hover:opacity-100">
                {onSupersede && (
                  <button
                    onClick={(e) => { e.stopPropagation(); onSupersede(d); }}
                    className="rounded bg-blue-500/10 px-1.5 py-0.5 text-[10px] font-medium text-blue-400 transition-colors hover:bg-blue-500/20"
                  >
                    Supersede
                  </button>
                )}
                {onArchive && (
                  <button
                    onClick={(e) => { e.stopPropagation(); onArchive(d); }}
                    className="rounded bg-white/5 px-1.5 py-0.5 text-[10px] font-medium text-zinc-400 transition-colors hover:bg-white/10"
                  >
                    Archive
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Active Contexts */}
      <h3 className="mt-6 text-xs font-semibold uppercase tracking-wide text-zinc-500">
        Active Contexts
      </h3>
      <div className="mt-2 space-y-1.5">
        {scopes.map((s) => (
          <div
            key={s}
            className="flex items-center gap-2 rounded-md border border-white/10 px-2.5 py-1.5 text-xs"
          >
            <span className="inline-block h-3 w-3 rounded bg-teal-500/15 text-center text-[8px] font-bold leading-3 text-teal-400">
              S
            </span>
            <code className="truncate text-zinc-400">{s}</code>
          </div>
        ))}
      </div>
    </aside>
  );
}
