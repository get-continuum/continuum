"use client";

import type { FactRecord } from "@/lib/api";

type Props = {
  facts: FactRecord[];
};

const CATEGORY_COLORS: Record<string, string> = {
  preference: "bg-blue-500/15 text-blue-400",
  constraint: "bg-amber-500/15 text-amber-400",
  rejection: "bg-red-500/15 text-red-400",
  interpretation: "bg-purple-500/15 text-purple-400",
  behavior_rule: "bg-emerald-500/15 text-emerald-400",
};

export default function FactsPanel({ facts }: Props) {
  if (facts.length === 0) return null;

  return (
    <div className="rounded-xl border border-white/[0.08] bg-[#111115] p-5 shadow-sm">
      <h2 className="text-sm font-semibold text-zinc-200">
        Extracted Facts
        <span className="ml-2 text-xs font-normal text-zinc-500">
          ({facts.length})
        </span>
      </h2>
      <div className="mt-3 space-y-2">
        {facts.map((fact) => (
          <div
            key={fact.id}
            className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-3"
          >
            <div className="flex items-center gap-2">
              <span
                className={[
                  "rounded-full px-2 py-0.5 text-[10px] font-bold uppercase",
                  CATEGORY_COLORS[fact.category] || "bg-zinc-500/15 text-zinc-400",
                ].join(" ")}
              >
                {fact.category}
              </span>
              <span className="text-[10px] text-zinc-500">
                {(fact.confidence * 100).toFixed(0)}% confidence
              </span>
            </div>
            <p className="mt-1.5 text-sm text-zinc-300">{fact.statement}</p>
            {fact.evidence.length > 0 && (
              <div className="mt-2 text-xs text-zinc-500 italic">
                &ldquo;{fact.evidence[0].quote}&rdquo;
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
