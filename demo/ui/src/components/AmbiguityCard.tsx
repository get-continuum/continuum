"use client";

import { useState } from "react";
import type { ResolveResult } from "@/lib/api";

type Props = {
  result: ResolveResult;
  prompt: string;
  loading: boolean;
  onCommit: (selectedId: string, selectedTitle: string, scope: string) => void;
  scopes: string[];
};

export default function AmbiguityCard({
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

  const candidates = result.clarification?.candidates || [];
  const question = result.clarification?.question || "No prior decision found. Define the intent to commit.";
  const hasCandidates = candidates.length > 0;

  const selectedCandidate = candidates.find((c) => c.id === selectedOption);

  const canCommit = hasCandidates ? !!selectedOption : customTitle.trim().length > 0;

  const handleCommit = () => {
    if (hasCandidates && selectedOption && selectedCandidate) {
      onCommit(selectedOption, selectedCandidate.title, applyScope);
    } else if (!hasCandidates && customTitle.trim()) {
      onCommit(`opt_custom_${Date.now()}`, customTitle.trim(), applyScope);
    }
  };

  return (
    <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 dark:border-amber-900/40 dark:bg-amber-950/30">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-lg">💡</span>
          <h3 className="text-sm font-semibold text-amber-900 dark:text-amber-200">
            Ambiguity Detected
          </h3>
        </div>
      </div>

      <p className="mt-2 text-sm text-amber-800 dark:text-amber-300">
        {question}
      </p>

      {hasCandidates ? (
        <div className="mt-3 space-y-2">
          {candidates.map((c) => (
            <label
              key={c.id}
              className={[
                "flex cursor-pointer items-center gap-3 rounded-lg border px-3 py-2 text-sm transition-colors",
                selectedOption === c.id
                  ? "border-amber-400 bg-amber-100 dark:border-amber-700 dark:bg-amber-900/40"
                  : "border-amber-200 bg-white hover:border-amber-300 dark:border-amber-900/30 dark:bg-amber-950/20",
              ].join(" ")}
            >
              <input
                type="radio"
                name="ambiguity-option"
                value={c.id}
                checked={selectedOption === c.id}
                onChange={() => setSelectedOption(c.id)}
                className="accent-amber-600"
              />
              <span>{c.title}</span>
            </label>
          ))}
        </div>
      ) : (
        <div className="mt-3">
          <label className="text-xs font-medium text-amber-800 dark:text-amber-300">
            Decision title
          </label>
          <input
            value={customTitle}
            onChange={(e) => setCustomTitle(e.target.value)}
            placeholder="e.g. Use bullet-point responses"
            className="mt-1 w-full rounded-lg border border-amber-200 bg-white px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-amber-400/30 dark:border-amber-900/30 dark:bg-amber-950/20"
          />
        </div>
      )}

      <div className="mt-4 flex items-center gap-3">
        <div className="flex items-center gap-1.5 text-xs text-zinc-600 dark:text-zinc-400">
          <span>Apply scope:</span>
          <select
            value={applyScope}
            onChange={(e) => setApplyScope(e.target.value)}
            className="rounded border border-zinc-200 bg-white px-2 py-0.5 text-xs dark:border-zinc-700 dark:bg-zinc-900"
          >
            {scopes.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
        <div className="ml-auto flex gap-2">
          <button
            disabled={!canCommit || loading}
            onClick={handleCommit}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-xs font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            Commit &amp; Continue
          </button>
        </div>
      </div>
    </div>
  );
}
