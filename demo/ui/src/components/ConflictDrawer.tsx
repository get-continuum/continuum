"use client";

import type { ConflictNote, DecisionRecord } from "@/lib/api";

type Props = {
  conflictNotes: ConflictNote[];
  decisions: DecisionRecord[];
  onClose: () => void;
};

export default function ConflictDrawer({
  conflictNotes,
  decisions,
  onClose,
}: Props) {
  if (conflictNotes.length === 0) return null;

  const findDecision = (id: string | undefined) =>
    decisions.find((d) => d.id === id);

  return (
    <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-5 animate-slideUp">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-lg">&#x26A0;</span>
          <h3 className="text-sm font-semibold text-amber-300">
            Competing Decisions Detected
          </h3>
        </div>
        <button
          onClick={onClose}
          className="flex h-7 w-7 items-center justify-center rounded-md text-zinc-500 transition-colors hover:bg-white/10 hover:text-zinc-200"
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M3.5 3.5L10.5 10.5M10.5 3.5L3.5 10.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </button>
      </div>

      {conflictNotes.map((note, idx) => {
        const winner = findDecision(note.winner_id);
        const losers = (note.loser_ids || [])
          .map(findDecision)
          .filter(Boolean) as DecisionRecord[];

        return (
          <div key={idx} className="mt-4">
            <p className="text-sm text-amber-400/80">{note.explanation}</p>

            <div className="mt-3 space-y-2">
              {/* Winner */}
              {winner && (
                <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-3">
                  <div className="flex items-center gap-2">
                    <span className="rounded-full bg-emerald-500/15 px-2 py-0.5 text-[10px] font-bold uppercase text-emerald-400">
                      Winner
                    </span>
                    <span className="text-sm font-medium text-zinc-200">
                      {winner.title}
                    </span>
                  </div>
                  <div className="mt-1 text-xs text-zinc-500">
                    <code>{winner.id}</code>
                    {note.scores && note.scores[winner.id] !== undefined && (
                      <span className="ml-2">
                        Score: {note.scores[winner.id].toFixed(1)}
                      </span>
                    )}
                  </div>
                </div>
              )}

              {/* Losers */}
              {losers.map((loser) => (
                <div
                  key={loser.id}
                  className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-3"
                >
                  <div className="flex items-center gap-2">
                    <span className="rounded-full bg-zinc-500/15 px-2 py-0.5 text-[10px] font-bold uppercase text-zinc-400">
                      Overridden
                    </span>
                    <span className="text-sm text-zinc-400">
                      {loser.title}
                    </span>
                  </div>
                  <div className="mt-1 text-xs text-zinc-600">
                    <code>{loser.id}</code>
                    {note.scores && note.scores[loser.id] !== undefined && (
                      <span className="ml-2">
                        Score: {note.scores[loser.id].toFixed(1)}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
