"use client";

import { useState } from "react";
import { COLAB_NOTEBOOK_URL } from "@/lib/constants";

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={async () => {
        await navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }}
      className="shrink-0 rounded-md border border-white/10 px-2.5 py-1 text-xs font-medium text-zinc-400 transition-colors hover:bg-white/5 hover:text-zinc-200"
    >
      {copied ? "Copied!" : "Copy"}
    </button>
  );
}

function CodeBlock({ code }: { code: string }) {
  return (
    <div className="relative mt-2">
      <pre className="overflow-auto rounded-lg border border-white/[0.06] bg-black/40 p-3 text-xs text-zinc-300">
        {code}
      </pre>
      <div className="absolute right-2 top-2">
        <CopyButton text={code} />
      </div>
    </div>
  );
}

export default function IntegrationsPage() {
  return (
    <div className="animate-fadeIn mx-auto max-w-3xl p-6">
      <h1 className="text-lg font-semibold text-white">Integrations</h1>
      <p className="mt-1 text-sm text-zinc-500">
        Connect Continuum to your tools and workflows.
      </p>

      <div className="mt-6 space-y-6">
        {/* Google Colab */}
        <div className="rounded-xl border border-amber-500/20 bg-amber-500/[0.04] p-4">
          <div className="flex items-center gap-2">
            <svg className="h-5 w-5 text-amber-500" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
            </svg>
            <h2 className="text-sm font-semibold text-zinc-200">
              Try in Google Colab
            </h2>
          </div>
          <p className="mt-1 text-xs text-zinc-500">
            Run the full Continuum workflow in your browser — no install
            required. Commit decisions, enforce actions, and see the ambiguity
            gate in under 5 minutes.
          </p>
          <a
            href={COLAB_NOTEBOOK_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-3 inline-flex items-center gap-2 rounded-lg bg-amber-500 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-amber-600"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 0 0 3 8.25v10.5A2.25 2.25 0 0 0 5.25 21h10.5A2.25 2.25 0 0 0 18 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
            </svg>
            Open in Colab
          </a>
        </div>

        {/* MCP Server */}
        <div className="rounded-xl border border-white/[0.08] bg-[#111115] p-4">
          <h2 className="text-sm font-semibold text-zinc-200">MCP Server (Cursor / Claude)</h2>
          <p className="mt-1 text-xs text-zinc-500">
            Expose Continuum decision tools to AI agents via the Model Context Protocol.
          </p>
          <CodeBlock code="pip install continuum-mcp-server" />
          <p className="mt-3 text-xs text-zinc-500">
            Add to your Cursor MCP config (<code className="text-zinc-400">~/.cursor/mcp.json</code>):
          </p>
          <CodeBlock
            code={JSON.stringify(
              { mcpServers: { continuum: { command: "continuum-mcp", args: ["serve"] } } },
              null,
              2
            )}
          />
        </div>

        {/* CLI */}
        <div className="rounded-xl border border-white/[0.08] bg-[#111115] p-4">
          <h2 className="text-sm font-semibold text-zinc-200">CLI</h2>
          <p className="mt-1 text-xs text-zinc-500">
            Inspect and manage decisions from the terminal.
          </p>
          <CodeBlock code="pip install continuum-cli" />
          <p className="mt-3 text-xs text-zinc-500">Usage:</p>
          <CodeBlock
            code={`continuum inspect --scope repo:my-project
continuum list --status active
continuum commit "Use UTC everywhere" --scope repo:my-project --type interpretation`}
          />
        </div>

        {/* Python SDK */}
        <div className="rounded-xl border border-white/[0.08] bg-[#111115] p-4">
          <h2 className="text-sm font-semibold text-zinc-200">Python SDK</h2>
          <p className="mt-1 text-xs text-zinc-500">
            Use Continuum in your Python applications.
          </p>
          <CodeBlock code="pip install continuum-sdk" />
          <CodeBlock
            code={`from continuum.client import ContinuumClient

client = ContinuumClient()
dec = client.commit(
    title="Use UTC everywhere",
    scope="repo:my-project",
    decision_type="interpretation",
    rationale="All timestamps should be in UTC.",
)
client.update_status(dec.id, "active")`}
          />
        </div>

        {/* TypeScript SDK */}
        <div className="rounded-xl border border-white/[0.08] bg-[#111115] p-4">
          <h2 className="text-sm font-semibold text-zinc-200">TypeScript SDK</h2>
          <p className="mt-1 text-xs text-zinc-500">
            Use Continuum in your TypeScript / Node.js applications.
          </p>
          <CodeBlock code="npm install @get-continuum/sdk" />
        </div>
      </div>
    </div>
  );
}
