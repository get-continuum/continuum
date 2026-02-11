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
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }, [authEnabled]);

  useEffect(() => { void refresh(); }, [refresh]);

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
    try { await revokeApiKey(keyId); await refresh(); }
    catch (e: unknown) { alert(e instanceof Error ? e.message : "Failed to revoke key"); }
  };

  const handleCopy = async (text: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="animate-fadeIn mx-auto max-w-3xl p-6">
      <h1 className="text-lg font-semibold text-white">Settings</h1>

      {/* Workspace Info */}
      <div className="mt-6 rounded-xl border border-white/[0.08] bg-[#111115] p-4">
        <h2 className="text-sm font-semibold text-zinc-200">Workspace</h2>
        <div className="mt-3 grid grid-cols-2 gap-4 text-sm">
          <div>
            <div className="text-xs font-medium text-zinc-500">Name</div>
            <div className="mt-0.5 text-zinc-300">{workspace?.name ?? "default"}</div>
          </div>
          <div>
            <div className="text-xs font-medium text-zinc-500">ID</div>
            <code className="mt-0.5 text-xs text-zinc-400">{workspace?.id ?? "ws_default"}</code>
          </div>
          {user && (
            <div>
              <div className="text-xs font-medium text-zinc-500">Email</div>
              <div className="mt-0.5 text-zinc-300">{user.email}</div>
            </div>
          )}
        </div>
      </div>

      {/* API Keys */}
      <div className="mt-6 rounded-xl border border-white/[0.08] bg-[#111115] p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-zinc-200">API Keys</h2>
        </div>

        {!authEnabled && (
          <p className="mt-3 text-sm text-zinc-500">
            API key management is available in hosted mode. Set{" "}
            <code className="text-zinc-400">CONTINUUM_AUTH_ENABLED=true</code> to enable.
          </p>
        )}

        {authEnabled && (
          <>
            <div className="mt-4 flex gap-2">
              <input
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") void handleCreate(); }}
                placeholder="Key name (e.g. cursor-mcp)"
                className="flex-1 rounded-md border border-white/10 bg-white/5 px-3 py-1.5 text-sm text-white placeholder-zinc-500 outline-none focus:border-teal-500/40 focus:ring-2 focus:ring-teal-500/20"
              />
              <button onClick={handleCreate} className="rounded-md bg-teal-600 px-4 py-1.5 text-sm font-medium text-white transition-colors hover:bg-teal-500">
                Create API Key
              </button>
            </div>

            {createdKey && (
              <div className="mt-3 rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-3">
                <div className="text-xs font-semibold text-emerald-400">
                  New API key created — copy it now, it won&apos;t be shown again:
                </div>
                <div className="mt-2 flex items-center gap-2">
                  <code className="flex-1 break-all rounded bg-white/5 px-2 py-1 text-xs text-zinc-300">{createdKey}</code>
                  <button onClick={() => handleCopy(createdKey)} className="shrink-0 rounded-md border border-white/10 px-3 py-1 text-xs font-medium text-zinc-300 transition-colors hover:bg-white/5">
                    {copied ? "Copied!" : "Copy"}
                  </button>
                </div>
              </div>
            )}

            <div className="mt-4 overflow-hidden rounded-lg border border-white/[0.08]">
              <table className="w-full text-sm">
                <thead className="bg-white/[0.03] text-left text-xs text-zinc-500">
                  <tr>
                    <th className="px-4 py-2 font-medium">Name</th>
                    <th className="px-4 py-2 font-medium">ID</th>
                    <th className="px-4 py-2 font-medium">Created</th>
                    <th className="px-4 py-2 font-medium" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.04]">
                  {loading && (
                    <tr><td colSpan={4} className="px-4 py-4 text-center text-zinc-500">Loading...</td></tr>
                  )}
                  {!loading && keys.length === 0 && (
                    <tr><td colSpan={4} className="px-4 py-4 text-center text-zinc-500">No API keys yet.</td></tr>
                  )}
                  {keys.map((k) => (
                    <tr key={k.id}>
                      <td className="px-4 py-2 text-zinc-300">{k.name}</td>
                      <td className="px-4 py-2"><code className="text-xs text-zinc-400">{k.id}</code></td>
                      <td className="px-4 py-2 text-zinc-500">{k.created_at ? new Date(k.created_at).toLocaleDateString() : "—"}</td>
                      <td className="px-4 py-2 text-right">
                        <button onClick={() => handleRevoke(k.id)} className="text-xs text-red-400 transition-colors hover:text-red-300">Revoke</button>
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
