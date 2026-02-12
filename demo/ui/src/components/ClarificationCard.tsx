"use client";

import { useState } from "react";
import type { ResolveResult } from "@/lib/api";

type CandidateWithPreview = {
  id: string;
  title: string;
  impact_preview?: string | null;
  source?: string;
  confidence?: number;
};

type Props = {
  result: ResolveResult;
  prompt: string;
  loading: boolean;
  onCommit: (chosenOptionId: string, title: string, scope: string) => void;
  scopes: string[];
};

export default function ClarificationCard({
  result,
  prompt,
  loading,
  onCommit,
  scopes,
}: Props) {
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [customTitle, setCustomTitle] = useState(prompt);
  const [applyScope, setApplyScope] = useState(scopes[0] || "");

  if (result.status !== "needs_clarification") return null;

  const clarification = result.clarification;
  const candidates: CandidateWithPreview[] =
    (clarification?.candidates as CandidateWithPreview[]) || [];
  const question =
    clarification?.question ||
    "No prior decision found. Define the intent to commit.";
  const hasCandidates = candidates.length > 0;
  const suggestedScope = (clarification as Record<string, unknown>)?.suggested_scope as string | undefined;

  const selectedCandidate = candidates.find((c) => c.id === selectedOption);
  const canCommit = hasCandidates
    ? !!selectedOption
    : customTitle.trim().length > 0;

  const handleCommit = () => {
    if (hasCandidates && selectedOption && selectedCandidate) {
      onCommit(selectedOption, selectedCandidate.title, applyScope);
    } else if (!hasCandidates && customTitle.trim()) {
      onCommit(`opt_custom_${Date.now()}`, customTitle.trim(), applyScope);
    }
  };

  return (
    <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4">
      <div className="flex items-center gap-2">
        <span className="text-lg">&#128161;</span>
        <h3 className="text-sm font-semibold text-amber-300">
          Clarification Needed
        </h3>
      </div>

      <p className="mt-2 text-sm text-amber-400/80">{question}</p>

      {hasCandidates ? (
        <div className="mt-3 space-y-2">
          {candidates.map((c) => (
            <label
              key={c.id}
              className={[
                "flex cursor-pointer flex-col gap-1 rounded-lg border px-3 py-2.5 text-sm transition-colors",
                selectedOption === c.id
                  ? "border-amber-500/30 bg-amber-500/10 text-white"
                  : "border-white/10 bg-white/[0.02] text-zinc-300 hover:border-white/15",
              ].join(" ")}
            >
              <div className="flex items-center gap-3">
                <input
                  type="radio"
                  name="clarification-option"
                  value={c.id}
                  checked={selectedOption === c.id}
                  onChange={() => setSelectedOption(c.id)}
                  className="accent-amber-500"
                />
                <span className="font-medium">{c.title}</span>
                {c.confidence !== undefined && (
                  <span className="ml-auto text-[10px] text-zinc-500">
                    {(c.confidence * 100).toFixed(0)}%
                  </span>
                )}
              </div>
              {c.impact_preview && (
                <p className="ml-7 text-xs text-zinc-500">
                  {c.impact_preview}
                </p>
              )}
            </label>
          ))}
        </div>
      ) : (
        <div className="mt-3">
          <label className="text-xs font-medium text-amber-400">
            Decision title
          </label>
          <input
            value={customTitle}
            onChange={(e) => setCustomTitle(e.target.value)}
            placeholder="e.g. Use bullet-point responses"
            className="mt-1 w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder-zinc-500 outline-none focus:border-amber-500/30 focus:ring-2 focus:ring-amber-500/20"
          />
        </div>
      )}

      <div className="mt-4 flex items-center gap-3">
        <div className="flex items-center gap-1.5 text-xs text-zinc-400">
          <span>Scope:</span>
          <select
            value={applyScope}
            onChange={(e) => setApplyScope(e.target.value)}
            className="rounded border border-white/10 bg-white/5 px-2 py-0.5 text-xs text-zinc-300"
          >
            {scopes.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
            {suggestedScope && !scopes.includes(suggestedScope) && (
              <option value={suggestedScope}>{suggestedScope} (suggested)</option>
            )}
          </select>
        </div>
        <div className="ml-auto flex gap-2">
          <button
            disabled={!canCommit || loading}
            onClick={handleCommit}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-xs font-medium text-white transition-colors hover:bg-emerald-500 disabled:opacity-50"
          >
            Commit Decision
          </button>
        </div>
      </div>
    </div>
  );
}
