"use client";

import { useState } from "react";

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={async () => {
        await navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }}
      className="shrink-0 rounded-md border border-zinc-200 px-2.5 py-1 text-xs font-medium hover:bg-zinc-50 dark:border-zinc-700 dark:hover:bg-zinc-900"
    >
      {copied ? "Copied!" : "Copy"}
    </button>
  );
}

function CodeBlock({ code }: { code: string }) {
  return (
    <div className="relative mt-2">
      <pre className="overflow-auto rounded-lg border border-zinc-200 bg-zinc-50 p-3 text-xs dark:border-zinc-800 dark:bg-black">
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
    <div className="mx-auto max-w-3xl p-6">
      <h1 className="text-lg font-semibold">Integrations</h1>
      <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
        Connect Continuum to your tools and workflows.
      </p>

      <div className="mt-6 space-y-6">
        {/* MCP Server */}
        <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
          <h2 className="text-sm font-semibold">MCP Server (Cursor / Claude)</h2>
          <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
            Expose Continuum decision tools to AI agents via the Model Context
            Protocol.
          </p>
          <CodeBlock code="pip install continuum-mcp-server" />
          <p className="mt-3 text-xs text-zinc-500 dark:text-zinc-400">
            Add to your Cursor MCP config (<code>~/.cursor/mcp.json</code>):
          </p>
          <CodeBlock
            code={JSON.stringify(
              {
                mcpServers: {
                  continuum: {
                    command: "continuum-mcp",
                    args: ["serve"],
                  },
                },
              },
              null,
              2
            )}
          />
        </div>

        {/* CLI */}
        <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
          <h2 className="text-sm font-semibold">CLI</h2>
          <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
            Inspect and manage decisions from the terminal.
          </p>
          <CodeBlock code="pip install continuum-cli" />
          <p className="mt-3 text-xs text-zinc-500 dark:text-zinc-400">
            Usage:
          </p>
          <CodeBlock
            code={`continuum inspect --scope repo:my-project
continuum list --status active
continuum commit "Use UTC everywhere" --scope repo:my-project --type interpretation`}
          />
        </div>

        {/* Python SDK */}
        <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
          <h2 className="text-sm font-semibold">Python SDK</h2>
          <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
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
        <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
          <h2 className="text-sm font-semibold">TypeScript SDK</h2>
          <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
            Use Continuum in your TypeScript / Node.js applications.
          </p>
          <CodeBlock code="npm install @get-continuum/sdk" />
        </div>
      </div>
    </div>
  );
}
