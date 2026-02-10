"use client";

import { useEffect, useMemo, useState } from "react";

type ResolveResult =
  | { status: "resolved"; resolved_context?: unknown; matched_decision_id?: string }
  | {
      status: "needs_clarification";
      clarification?: { question: string; candidates: Array<{ id: string; title: string }> };
    };

type ChatMsg = { role: "user" | "system"; text: string };

type DecisionRecord = {
  id: string;
  title: string;
  status: string;
  version?: number;
  rationale?: string;
  options_considered?: Array<{ id: string; title: string; selected: boolean; rejected_reason?: string }>;
  enforcement?: { scope?: string; decision_type?: string; supersedes?: string; override_policy?: string; [k: string]: unknown };
  created_at?: string;
  updated_at?: string;
  [k: string]: unknown;
};

type EnforcementResult = {
  verdict: string;
  reason: string;
  matched_decisions?: string[];
  required_confirmations?: string[];
  [k: string]: unknown;
};

const DEFAULT_CANDIDATES = [
  { id: "opt_tests_errors", title: "Add tests + error handling (repo standard)" },
  { id: "opt_enterprise", title: "Enterprise hardening (observability, SLOs, etc.)" },
];

function apiBase(): string {
  return process.env.NEXT_PUBLIC_CONTINUUM_API || "http://localhost:8787";
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${apiBase()}${path}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return (await res.json()) as T;
}

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${apiBase()}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  return (await res.json()) as T;
}

export default function Home() {
  const [scope, setScope] = useState("repo:continuum-demo");
  const [prompt, setPrompt] = useState("Make it production-ready");
  const [chat, setChat] = useState<ChatMsg[]>([
    {
      role: "system",
      text: "Continuum demo: ambiguity gate + decision inspector + enforcement.",
    },
  ]);

  const [binding, setBinding] = useState<DecisionRecord[]>([]);
  const [lastResolution, setLastResolution] = useState<ResolveResult | null>(null);
  const [lastEnforcement, setLastEnforcement] = useState<EnforcementResult | null>(null);
  const [selectedDecision, setSelectedDecision] = useState<DecisionRecord | null>(null);
  const [loading, setLoading] = useState(false);
  const clarificationCandidates = useMemo(() => {
    if (lastResolution?.status === "needs_clarification") {
      return lastResolution.clarification?.candidates || [];
    }
    return [];
  }, [lastResolution]);

  async function refreshInspector() {
    const data = await getJson<{ binding: DecisionRecord[] }>(
      `/inspect?scope=${encodeURIComponent(scope)}`
    );
    setBinding(data.binding ?? []);
  }

  useEffect(() => {
    void refreshInspector();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scope]);

  async function seedRejectionDecision() {
    setLoading(true);
    try {
      await postJson("/commit", {
        title: "Reject full rewrites in this repo",
        scope,
        decision_type: "rejection",
        rationale: "Prefer incremental refactors to reduce risk and review cost.",
        options: [
          { title: "Incremental refactor", selected: true },
          { title: "Full rewrite", selected: false, rejected_reason: "Too risky; prefer incremental refactors." },
        ],
        activate: true,
      });
      setChat((c) => [...c, { role: "system", text: "Seeded: rejection decision (no full rewrites)." }]);
      await refreshInspector();
    } finally {
      setLoading(false);
    }
  }

  async function sendPrompt() {
    const p = prompt.trim();
    if (!p) return;

    setChat((c) => [...c, { role: "user", text: p }]);
    setPrompt("");
    setLoading(true);
    setLastEnforcement(null);

    try {
      const body = {
        prompt: p,
        scope,
        candidates: p.toLowerCase().includes("production-ready") ? DEFAULT_CANDIDATES : undefined,
      };
      const data = await postJson<{ resolution: ResolveResult }>("/resolve", body);
      setLastResolution(data.resolution);

      if (data.resolution.status === "resolved") {
        setChat((c) => [
          ...c,
          {
            role: "system",
            text: `Resolved by prior decision: ${data.resolution.matched_decision_id ?? "unknown"}`,
          },
        ]);
      } else {
        setChat((c) => [
          ...c,
          { role: "system", text: "Ambiguity Gate: needs clarification (pick an option to promote to a decision)." },
        ]);
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setChat((c) => [...c, { role: "system", text: `Error: ${msg}` }]);
    } finally {
      setLoading(false);
      await refreshInspector();
    }
  }

  async function promoteInterpretation(selectedOptionId: string, selectedTitle: string) {
    setLoading(true);
    try {
      await postJson("/commit", {
        title: "production-ready",
        scope,
        decision_type: "interpretation",
        rationale: `In this repo, production-ready means: ${selectedTitle}.`,
        metadata: { selected_option_id: selectedOptionId },
        activate: true,
      });
      setChat((c) => [
        ...c,
        { role: "system", text: `Promoted to decision: production-ready -> ${selectedTitle}` },
      ]);
      setLastResolution(null);
      await refreshInspector();
    } finally {
      setLoading(false);
    }
  }

  async function tryFullRewrite() {
    setLoading(true);
    try {
      const data = await postJson<{ enforcement: EnforcementResult }>("/enforce", {
        scope,
        action: { type: "code_change", description: "Do a full rewrite of auth module" },
      });
      setLastEnforcement(data.enforcement);
      setChat((c) => [
        ...c,
        { role: "system", text: `Enforcement verdict: ${data.enforcement.verdict} (${data.enforcement.reason})` },
      ]);
    } finally {
      setLoading(false);
      await refreshInspector();
    }
  }

  async function supersedeProductionReady() {
    const active = binding.find((d) => d?.title === "production-ready" && d?.status === "active");
    if (!active?.id) {
      setChat((c) => [...c, { role: "system", text: "No active production-ready decision found to supersede." }]);
      return;
    }
    setLoading(true);
    try {
      await postJson("/supersede", {
        old_id: active.id,
        new_title: "production-ready",
        rationale: "Production-ready now includes linting.",
        metadata: { selected_option_id: "opt_tests_errors_lint" },
      });
      setChat((c) => [...c, { role: "system", text: `Superseded decision ${active.id} -> new active version.` }]);
      await refreshInspector();
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-900 dark:bg-black dark:text-zinc-50">
      <div className="mx-auto max-w-6xl px-6 py-8">
        <div className="mb-6 flex items-start justify-between gap-6">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Continuum</h1>
            <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
              Decision Control Plane for AI Agents &mdash; Ambiguity Gate + Decision Inspector
            </p>
          </div>
          <div className="w-full max-w-md">
            <label className="text-xs font-medium text-zinc-600 dark:text-zinc-400">Scope</label>
            <input
              value={scope}
              onChange={(e) => setScope(e.target.value)}
              className="mt-1 w-full rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm shadow-sm outline-none focus:ring-2 focus:ring-zinc-900/10 dark:border-zinc-800 dark:bg-zinc-950"
              placeholder="repo:acme/backend/folder:src/api/auth"
            />
            <div className="mt-2 flex gap-2">
              <button
                onClick={seedRejectionDecision}
                disabled={loading}
                className="rounded-md bg-zinc-900 px-3 py-2 text-xs font-medium text-white hover:bg-zinc-800 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
              >
                Seed demo decisions
              </button>
              <button
                onClick={tryFullRewrite}
                disabled={loading}
                className="rounded-md border border-zinc-200 bg-white px-3 py-2 text-xs font-medium hover:bg-zinc-50 disabled:opacity-50 dark:border-zinc-800 dark:bg-zinc-950 dark:hover:bg-zinc-900"
              >
                Try full rewrite
              </button>
              <button
                onClick={supersedeProductionReady}
                disabled={loading}
                className="rounded-md border border-zinc-200 bg-white px-3 py-2 text-xs font-medium hover:bg-zinc-50 disabled:opacity-50 dark:border-zinc-800 dark:bg-zinc-950 dark:hover:bg-zinc-900"
              >
                Supersede production-ready
              </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
          {/* Chat */}
          <div className="lg:col-span-3 rounded-xl border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold">Chat</h2>
              <span className="text-xs text-zinc-500">{loading ? "working..." : "idle"}</span>
            </div>
            <div className="mt-4 h-[440px] overflow-auto rounded-lg border border-zinc-100 bg-zinc-50 p-3 text-sm dark:border-zinc-900 dark:bg-black">
              <div className="space-y-3">
                {chat.map((m, idx) => (
                  <div key={idx} className={m.role === "user" ? "text-right" : "text-left"}>
                    <div
                      className={[
                        "inline-block max-w-[85%] rounded-2xl px-3 py-2",
                        m.role === "user"
                          ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
                          : "bg-white text-zinc-900 border border-zinc-200 dark:bg-zinc-950 dark:text-zinc-50 dark:border-zinc-800",
                      ].join(" ")}
                    >
                      {m.text}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Ambiguity Gate */}
            {clarificationCandidates.length > 0 && (
              <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-3 dark:border-amber-900/40 dark:bg-amber-950/30">
                <div className="text-xs font-semibold text-amber-900 dark:text-amber-200">Ambiguity Gate</div>
                <div className="mt-1 text-xs text-amber-800 dark:text-amber-300">
                  {lastResolution?.status === "needs_clarification"
                    ? lastResolution.clarification?.question
                    : null}
                </div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {clarificationCandidates.map((c) => (
                    <button
                      key={c.id}
                      disabled={loading}
                      onClick={() => promoteInterpretation(c.id, c.title)}
                      className="rounded-md bg-amber-900 px-3 py-2 text-xs font-medium text-white hover:bg-amber-800 disabled:opacity-50 dark:bg-amber-200 dark:text-amber-950"
                    >
                      {c.title}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Composer */}
            <div className="mt-4 flex gap-2">
              <input
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) void sendPrompt();
                }}
                className="w-full rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm shadow-sm outline-none focus:ring-2 focus:ring-zinc-900/10 dark:border-zinc-800 dark:bg-zinc-950"
                placeholder="Ask: Make it production-ready"
              />
              <button
                onClick={sendPrompt}
                disabled={loading}
                className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
              >
                Send
              </button>
            </div>
          </div>

          {/* Right panel: Inspector + Artifact */}
          <div className="lg:col-span-2 space-y-4">
            {/* Decision Inspector */}
            <div className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold">Decision Inspector</h2>
                <button
                  onClick={refreshInspector}
                  disabled={loading}
                  className="text-xs text-zinc-600 hover:text-zinc-900 disabled:opacity-50 dark:text-zinc-400 dark:hover:text-zinc-50"
                >
                  Refresh
                </button>
              </div>

              <div className="mt-3 text-xs text-zinc-600 dark:text-zinc-400">
                Active binding set for <code>{scope}</code>
                <span className="ml-2 font-medium">{binding.length} decision{binding.length !== 1 ? "s" : ""}</span>
              </div>

              <div className="mt-3 max-h-[260px] space-y-2 overflow-auto">
                {binding.length === 0 ? (
                  <div className="rounded-lg border border-zinc-100 bg-zinc-50 p-3 text-sm text-zinc-600 dark:border-zinc-900 dark:bg-black dark:text-zinc-400">
                    No active decisions yet. Click &quot;Seed demo decisions&quot;.
                  </div>
                ) : (
                  binding.map((d) => (
                    <button
                      key={d.id}
                      onClick={() => setSelectedDecision(d)}
                      className={[
                        "w-full text-left rounded-lg border p-3 text-sm transition-colors",
                        selectedDecision?.id === d.id
                          ? "border-zinc-900 bg-zinc-100 dark:border-zinc-100 dark:bg-zinc-900"
                          : "border-zinc-100 bg-zinc-50 hover:border-zinc-300 dark:border-zinc-900 dark:bg-black dark:hover:border-zinc-700",
                      ].join(" ")}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="font-medium">{d.title}</div>
                        <span className={[
                          "shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium",
                          d.status === "active" ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400"
                          : d.status === "superseded" ? "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400"
                          : "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400",
                        ].join(" ")}>{d.status}</span>
                      </div>
                      <div className="mt-1 text-[11px] text-zinc-600 dark:text-zinc-400">
                        <code>{d.id}</code>
                        {d.enforcement?.decision_type && (
                          <span className="ml-2 rounded bg-zinc-200 px-1.5 py-0.5 dark:bg-zinc-800">{d.enforcement.decision_type}</span>
                        )}
                        {d.enforcement?.supersedes && (
                          <span className="ml-2 text-amber-600 dark:text-amber-400">supersedes {d.enforcement.supersedes.slice(0, 16)}...</span>
                        )}
                      </div>
                    </button>
                  ))
                )}
              </div>

              {lastEnforcement ? (
                <div className={[
                  "mt-4 rounded-lg border p-3 text-sm",
                  lastEnforcement.verdict === "block"
                    ? "border-red-200 bg-red-50 dark:border-red-900/40 dark:bg-red-950/30"
                    : lastEnforcement.verdict === "confirm"
                    ? "border-amber-200 bg-amber-50 dark:border-amber-900/40 dark:bg-amber-950/30"
                    : "border-emerald-200 bg-emerald-50 dark:border-emerald-900/40 dark:bg-emerald-950/30",
                ].join(" ")}>
                  <div className="text-xs font-semibold">Enforcement Result</div>
                  <div className="mt-1 flex items-center gap-2">
                    <span className={[
                      "rounded-full px-2 py-0.5 text-[10px] font-bold uppercase",
                      lastEnforcement.verdict === "block" ? "bg-red-200 text-red-900 dark:bg-red-900/50 dark:text-red-300"
                      : lastEnforcement.verdict === "confirm" ? "bg-amber-200 text-amber-900 dark:bg-amber-900/50 dark:text-amber-300"
                      : "bg-emerald-200 text-emerald-900 dark:bg-emerald-900/50 dark:text-emerald-300",
                    ].join(" ")}>{lastEnforcement.verdict}</span>
                    <span className="text-xs text-zinc-600 dark:text-zinc-400">{lastEnforcement.reason}</span>
                  </div>
                </div>
              ) : null}
            </div>

            {/* Decision Artifact */}
            {selectedDecision && (
              <div className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
                <div className="flex items-center justify-between">
                  <h2 className="text-sm font-semibold">Decision Artifact</h2>
                  <button
                    onClick={() => setSelectedDecision(null)}
                    className="text-xs text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-50"
                  >
                    Close
                  </button>
                </div>
                <div className="mt-3 space-y-3 text-xs">
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <div className="font-medium text-zinc-500 dark:text-zinc-400">ID</div>
                      <code className="text-zinc-900 dark:text-zinc-100">{selectedDecision.id}</code>
                    </div>
                    <div>
                      <div className="font-medium text-zinc-500 dark:text-zinc-400">Version</div>
                      <span>v{selectedDecision.version ?? 0}</span>
                    </div>
                    <div>
                      <div className="font-medium text-zinc-500 dark:text-zinc-400">Type</div>
                      <span className="rounded bg-zinc-200 px-1.5 py-0.5 dark:bg-zinc-800">
                        {selectedDecision.enforcement?.decision_type ?? "unknown"}
                      </span>
                    </div>
                    <div>
                      <div className="font-medium text-zinc-500 dark:text-zinc-400">Scope</div>
                      <code>{selectedDecision.enforcement?.scope ?? "unknown"}</code>
                    </div>
                    <div>
                      <div className="font-medium text-zinc-500 dark:text-zinc-400">Override Policy</div>
                      <span>{selectedDecision.enforcement?.override_policy ?? "invalid_by_default"}</span>
                    </div>
                    <div>
                      <div className="font-medium text-zinc-500 dark:text-zinc-400">Status</div>
                      <span>{selectedDecision.status}</span>
                    </div>
                  </div>

                  {selectedDecision.rationale && (
                    <div>
                      <div className="font-medium text-zinc-500 dark:text-zinc-400">Rationale</div>
                      <div className="mt-1 rounded-lg border border-zinc-100 bg-zinc-50 p-2 text-zinc-800 dark:border-zinc-900 dark:bg-black dark:text-zinc-200">
                        {selectedDecision.rationale}
                      </div>
                    </div>
                  )}

                  {selectedDecision.options_considered && selectedDecision.options_considered.length > 0 && (
                    <div>
                      <div className="font-medium text-zinc-500 dark:text-zinc-400">Options Considered</div>
                      <div className="mt-1 space-y-1">
                        {selectedDecision.options_considered.map((opt) => (
                          <div
                            key={opt.id}
                            className={[
                              "flex items-center gap-2 rounded-md border px-2 py-1.5",
                              opt.selected
                                ? "border-emerald-200 bg-emerald-50 dark:border-emerald-900/40 dark:bg-emerald-950/30"
                                : "border-zinc-100 bg-zinc-50 dark:border-zinc-900 dark:bg-black",
                            ].join(" ")}
                          >
                            <span className={opt.selected ? "text-emerald-600 dark:text-emerald-400" : "text-zinc-400"}>
                              {opt.selected ? "+" : "-"}
                            </span>
                            <span className={opt.selected ? "font-medium" : "line-through opacity-60"}>
                              {opt.title}
                            </span>
                            {opt.rejected_reason && (
                              <span className="ml-auto text-[10px] text-zinc-500">({opt.rejected_reason})</span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {selectedDecision.enforcement?.supersedes && (
                    <div className="rounded-lg border border-amber-200 bg-amber-50 p-2 dark:border-amber-900/40 dark:bg-amber-950/30">
                      <span className="font-medium text-amber-800 dark:text-amber-300">Supersedes:</span>{" "}
                      <code className="text-amber-900 dark:text-amber-200">{selectedDecision.enforcement.supersedes}</code>
                    </div>
                  )}

                  {selectedDecision.created_at && (
                    <div className="text-[10px] text-zinc-400">
                      Created: {new Date(selectedDecision.created_at).toLocaleString()}
                      {selectedDecision.updated_at && selectedDecision.updated_at !== selectedDecision.created_at && (
                        <> | Updated: {new Date(selectedDecision.updated_at).toLocaleString()}</>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
