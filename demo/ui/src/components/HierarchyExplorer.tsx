"use client";

import { useState } from "react";
import type { DecisionRecord } from "@/lib/api";
import { parseScope, timeAgo, cn } from "@/lib/utils";

type Props = {
  decision: DecisionRecord;
  onClose?: () => void;
  onSupersede?: () => void;
  onArchive?: () => void;
};

/* ------------------------------------------------------------------ */
/*  Collapsible Section                                                */
/* ------------------------------------------------------------------ */

function Section({
  title,
  defaultOpen = true,
  children,
}: {
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border-b border-white/[0.06] last:border-b-0">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-2 px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500 transition-colors hover:text-zinc-300"
      >
        <svg
          width="12"
          height="12"
          viewBox="0 0 12 12"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className={cn(
            "shrink-0 transition-transform",
            open && "rotate-90"
          )}
        >
          <path
            d="M4.5 2.5L8 6L4.5 9.5"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        {title}
      </button>
      {open && <div className="px-4 pb-4">{children}</div>}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Status pill                                                        */
/* ------------------------------------------------------------------ */

function StatusPill({ status }: { status: string }) {
  const colors: Record<string, string> = {
    active:
      "bg-emerald-500/15 text-emerald-400 border border-emerald-500/20",
    superseded:
      "bg-amber-500/15 text-amber-400 border border-amber-500/20",
    archived:
      "bg-red-500/15 text-red-400 border border-red-500/20",
    draft:
      "bg-zinc-500/15 text-zinc-400 border border-zinc-500/20",
  };
  return (
    <span
      className={cn(
        "inline-block rounded-full px-2 py-0.5 text-[10px] font-medium",
        colors[status] || colors.draft
      )}
    >
      {status}
    </span>
  );
}

/* ------------------------------------------------------------------ */
/*  Scope type color mapping                                           */
/* ------------------------------------------------------------------ */

const SCOPE_TYPE_COLORS: Record<string, string> = {
  repo: "bg-blue-500/15 text-blue-400",
  folder: "bg-purple-500/15 text-purple-400",
  user: "bg-emerald-500/15 text-emerald-400",
  workflow: "bg-amber-500/15 text-amber-400",
  team: "bg-rose-500/15 text-rose-400",
  scope: "bg-zinc-500/15 text-zinc-400",
};

/* ------------------------------------------------------------------ */
/*  Key-value table row                                                */
/* ------------------------------------------------------------------ */

function KVRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <tr className="border-b border-white/[0.04] last:border-b-0">
      <td className="whitespace-nowrap py-2 pr-6 text-xs font-medium text-zinc-500">
        {label}
      </td>
      <td className="py-2 text-xs text-zinc-300">
        {value}
      </td>
    </tr>
  );
}

/* ------------------------------------------------------------------ */
/*  Main component                                                     */
/* ------------------------------------------------------------------ */

export default function HierarchyExplorer({
  decision,
  onClose,
  onSupersede,
  onArchive,
}: Props) {
  const enforcement = decision.enforcement;
  const scopeLevels = parseScope(enforcement?.scope || "");

  return (
    <div className="animate-slideUp overflow-hidden rounded-xl border border-white/[0.08] bg-[#111115] shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/[0.06] px-4 py-3">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-white">
            {decision.title}
          </h3>
          <StatusPill status={decision.status} />
        </div>
        <div className="flex items-center gap-2">
          {onSupersede && decision.status === "active" && (
            <button
              onClick={onSupersede}
              className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-blue-500"
            >
              Supersede
            </button>
          )}
          {onArchive && decision.status === "active" && (
            <button
              onClick={onArchive}
              className="rounded-lg border border-white/10 px-3 py-1.5 text-xs font-medium text-zinc-400 transition-colors hover:bg-white/5 hover:text-zinc-200"
            >
              Archive
            </button>
          )}
          {onClose && (
            <button
              onClick={onClose}
              className="flex h-7 w-7 items-center justify-center rounded-md text-zinc-500 transition-colors hover:bg-white/10 hover:text-zinc-200"
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M3.5 3.5L10.5 10.5M10.5 3.5L3.5 10.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Scope Hierarchy */}
      {scopeLevels.length > 0 && (
        <Section title="Scope Hierarchy" defaultOpen={true}>
          <div className="overflow-hidden rounded-lg border border-white/[0.06]">
            <table className="w-full text-xs">
              <thead className="bg-white/[0.03] text-left text-zinc-500">
                <tr>
                  <th className="px-3 py-2 font-medium">Level</th>
                  <th className="px-3 py-2 font-medium">Scope Type</th>
                  <th className="px-3 py-2 font-medium">Value</th>
                  <th className="px-3 py-2 font-medium">Specificity</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {scopeLevels.map((lvl) => (
                  <tr key={lvl.level}>
                    <td className="px-3 py-2 text-zinc-400">{lvl.level}</td>
                    <td className="px-3 py-2">
                      <span
                        className={cn(
                          "inline-block rounded-full px-2 py-0.5 text-[10px] font-medium",
                          SCOPE_TYPE_COLORS[lvl.type] || SCOPE_TYPE_COLORS.scope
                        )}
                      >
                        {lvl.type}
                      </span>
                    </td>
                    <td className="px-3 py-2">
                      <code className="text-zinc-300">{lvl.value}</code>
                    </td>
                    <td className="px-3 py-2 text-zinc-500">{lvl.specificity}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>
      )}

      {/* Overview */}
      <Section title="Overview" defaultOpen={true}>
        <table className="w-full">
          <tbody>
            <KVRow
              label="ID"
              value={
                <code className="rounded bg-white/5 px-1.5 py-0.5 text-[11px] text-zinc-300">
                  {decision.id}
                </code>
              }
            />
            <KVRow label="Title" value={decision.title} />
            <KVRow label="Status" value={<StatusPill status={decision.status} />} />
            <KVRow label="Version" value={decision.version ?? 0} />
            {decision.created_at && (
              <KVRow
                label="Created"
                value={`${timeAgo(decision.created_at)} (${new Date(decision.created_at).toLocaleString()})`}
              />
            )}
            {decision.updated_at && decision.updated_at !== decision.created_at && (
              <KVRow
                label="Updated"
                value={`${timeAgo(decision.updated_at)} (${new Date(decision.updated_at).toLocaleString()})`}
              />
            )}
          </tbody>
        </table>
      </Section>

      {/* Rationale */}
      {decision.rationale && (
        <Section title="Rationale" defaultOpen={true}>
          <p className="rounded-lg border border-white/[0.06] bg-white/[0.03] p-3 text-sm leading-relaxed text-zinc-300">
            {decision.rationale}
          </p>
        </Section>
      )}

      {/* Enforcement */}
      {enforcement && (
        <Section title="Enforcement" defaultOpen={true}>
          <table className="w-full">
            <tbody>
              {enforcement.scope && (
                <KVRow label="Scope" value={<code className="text-zinc-300">{enforcement.scope}</code>} />
              )}
              {enforcement.decision_type && (
                <KVRow
                  label="Decision Type"
                  value={
                    <span className="rounded-full bg-teal-500/15 px-2 py-0.5 text-[10px] font-medium text-teal-400">
                      {enforcement.decision_type}
                    </span>
                  }
                />
              )}
              {enforcement.supersedes && (
                <KVRow
                  label="Supersedes"
                  value={<code className="text-amber-400">{enforcement.supersedes}</code>}
                />
              )}
              {enforcement.override_policy && (
                <KVRow label="Override Policy" value={enforcement.override_policy} />
              )}
            </tbody>
          </table>
        </Section>
      )}

      {/* Options Considered */}
      {decision.options_considered && decision.options_considered.length > 0 && (
        <Section title="Options Considered" defaultOpen={true}>
          <div className="overflow-hidden rounded-lg border border-white/[0.06]">
            <table className="w-full text-xs">
              <thead className="bg-white/[0.03] text-left text-zinc-500">
                <tr>
                  <th className="px-3 py-2 font-medium">Option</th>
                  <th className="px-3 py-2 font-medium">Selected</th>
                  <th className="px-3 py-2 font-medium">Rejected Reason</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {decision.options_considered.map((opt) => (
                  <tr key={opt.id}>
                    <td className="px-3 py-2 font-medium text-zinc-300">{opt.title}</td>
                    <td className="px-3 py-2">
                      {opt.selected ? (
                        <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500/15 text-emerald-400">
                          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                            <path d="M2.5 6L5 8.5L9.5 3.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
                        </span>
                      ) : (
                        <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-red-500/15 text-red-400">
                          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                            <path d="M3 3L9 9M9 3L3 9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                          </svg>
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-zinc-500">{opt.rejected_reason || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>
      )}

      {/* Metadata */}
      {decision.metadata && Object.keys(decision.metadata).length > 0 && (
        <Section title="Metadata" defaultOpen={false}>
          <div className="overflow-hidden rounded-lg border border-white/[0.06]">
            <table className="w-full text-xs">
              <thead className="bg-white/[0.03] text-left text-zinc-500">
                <tr>
                  <th className="px-3 py-2 font-medium">Key</th>
                  <th className="px-3 py-2 font-medium">Value</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {Object.entries(decision.metadata).map(([key, value]) => (
                  <tr key={key}>
                    <td className="px-3 py-2 font-medium text-zinc-400">{key}</td>
                    <td className="px-3 py-2 text-zinc-300">
                      {typeof value === "object" ? JSON.stringify(value) : String(value)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>
      )}
    </div>
  );
}
