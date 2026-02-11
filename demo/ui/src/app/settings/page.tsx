"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import { isAuthEnabled } from "@/lib/auth";
import { fetchApiKeys, createApiKey, revokeApiKey } from "@/lib/api";
import type { ApiKey } from "@/lib/api";

export default function SettingsPage() {
  const { workspace, user } = useAuth();
  const authEnabled = isAuthEnabled();
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const refresh = useCallback(async () => {
    if (!authEnabled) return;
    setLoading(true);
    try {
      const data = await fetchApiKeys();
      setKeys(data.keys ?? []);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, [authEnabled]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const handleCreate = async () => {
    const name = newKeyName.trim() || "default";
    try {
      const data = await createApiKey(name);
      setCreatedKey(data.raw_key);
      setNewKeyName("");
      setCopied(false);
      await refresh();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Failed to create key");
    }
  };

  const handleRevoke = async (keyId: string) => {
    if (!confirm("Are you sure you want to revoke this API key?")) return;
    try {
      await revokeApiKey(keyId);
      await refresh();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Failed to revoke key");
    }
  };

  const handleCopy = async (text: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="mx-auto max-w-3xl p-6">
      <h1 className="text-lg font-semibold">Settings</h1>

      {/* Workspace Info */}
      <div className="mt-6 rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
        <h2 className="text-sm font-semibold">Workspace</h2>
        <div className="mt-3 grid grid-cols-2 gap-4 text-sm">
          <div>
            <div className="text-xs font-medium text-zinc-500 dark:text-zinc-400">
              Name
            </div>
            <div className="mt-0.5">{workspace?.name ?? "default"}</div>
          </div>
          <div>
            <div className="text-xs font-medium text-zinc-500 dark:text-zinc-400">
              ID
            </div>
            <code className="mt-0.5 text-xs">{workspace?.id ?? "ws_default"}</code>
          </div>
          {user && (
            <div>
              <div className="text-xs font-medium text-zinc-500 dark:text-zinc-400">
                Email
              </div>
              <div className="mt-0.5">{user.email}</div>
            </div>
          )}
        </div>
      </div>

      {/* API Keys */}
      <div className="mt-6 rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold">API Keys</h2>
        </div>

        {!authEnabled && (
          <p className="mt-3 text-sm text-zinc-500">
            API key management is available in hosted mode. Set{" "}
            <code>CONTINUUM_AUTH_ENABLED=true</code> to enable.
          </p>
        )}

        {authEnabled && (
          <>
            {/* Create key */}
            <div className="mt-4 flex gap-2">
              <input
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") void handleCreate();
                }}
                placeholder="Key name (e.g. cursor-mcp)"
                className="flex-1 rounded-md border border-zinc-200 px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-teal-500/30 dark:border-zinc-800 dark:bg-zinc-950"
              />
              <button
                onClick={handleCreate}
                className="rounded-md bg-teal-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-teal-700"
              >
                Create API Key
              </button>
            </div>

            {/* Show created key once */}
            {createdKey && (
              <div className="mt-3 rounded-lg border border-emerald-200 bg-emerald-50 p-3 dark:border-emerald-900/40 dark:bg-emerald-950/30">
                <div className="text-xs font-semibold text-emerald-800 dark:text-emerald-300">
                  New API key created — copy it now, it won&apos;t be shown again:
                </div>
                <div className="mt-2 flex items-center gap-2">
                  <code className="flex-1 break-all rounded bg-white px-2 py-1 text-xs dark:bg-black">
                    {createdKey}
                  </code>
                  <button
                    onClick={() => handleCopy(createdKey)}
                    className="shrink-0 rounded-md border border-zinc-200 px-3 py-1 text-xs font-medium hover:bg-zinc-50 dark:border-zinc-700"
                  >
                    {copied ? "Copied!" : "Copy"}
                  </button>
                </div>
              </div>
            )}

            {/* Keys table */}
            <div className="mt-4 overflow-hidden rounded-lg border border-zinc-200 dark:border-zinc-800">
              <table className="w-full text-sm">
                <thead className="bg-zinc-50 text-left text-xs text-zinc-500 dark:bg-zinc-900 dark:text-zinc-400">
                  <tr>
                    <th className="px-4 py-2 font-medium">Name</th>
                    <th className="px-4 py-2 font-medium">ID</th>
                    <th className="px-4 py-2 font-medium">Created</th>
                    <th className="px-4 py-2 font-medium" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
                  {loading && (
                    <tr>
                      <td colSpan={4} className="px-4 py-4 text-center text-zinc-400">
                        Loading...
                      </td>
                    </tr>
                  )}
                  {!loading && keys.length === 0 && (
                    <tr>
                      <td colSpan={4} className="px-4 py-4 text-center text-zinc-400">
                        No API keys yet.
                      </td>
                    </tr>
                  )}
                  {keys.map((k) => (
                    <tr key={k.id}>
                      <td className="px-4 py-2">{k.name}</td>
                      <td className="px-4 py-2">
                        <code className="text-xs">{k.id}</code>
                      </td>
                      <td className="px-4 py-2 text-zinc-500">
                        {k.created_at
                          ? new Date(k.created_at).toLocaleDateString()
                          : "—"}
                      </td>
                      <td className="px-4 py-2 text-right">
                        <button
                          onClick={() => handleRevoke(k.id)}
                          className="text-xs text-red-600 hover:text-red-800 dark:text-red-400"
                        >
                          Revoke
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
